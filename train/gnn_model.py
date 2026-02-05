import torch
import torch.nn as nn
import torch.nn.functional as F
from ray.rllib.models.torch.torch_modelv2 import TorchModelV2
from ray.rllib.utils.annotations import override

class GraphAttentionLayer(nn.Module):
    def __init__(self, in_features, out_features, dropout=0.1, alpha=0.2):
        super(GraphAttentionLayer, self).__init__()
        self.W = nn.Parameter(torch.zeros(size=(in_features, out_features)))
        nn.init.xavier_uniform_(self.W.data, gain=1.414)
        self.a = nn.Parameter(torch.zeros(size=(2*out_features, 1)))
        nn.init.xavier_uniform_(self.a.data, gain=1.414)
        self.leakyrelu = nn.LeakyReLU(alpha)

    def forward(self, h, adj):
        Wh = torch.matmul(h, self.W) # [B, N, Out]
        B, N, _ = Wh.size()
        
        # Self-attention mechanism
        Wh_repeated_in_chunks = Wh.repeat_interleave(N, dim=1)
        Wh_repeated_alternating = Wh.repeat(1, N, 1)
        out_f = Wh.size(2)
        a_input = torch.cat([Wh_repeated_in_chunks, Wh_repeated_alternating], dim=2).view(B, N, N, 2 * out_f)
        # Fix: correctly calculate shapes for concatenated attention
        out_f = Wh.size(2)
        a_input = torch.cat([Wh_repeated_in_chunks, Wh_repeated_alternating], dim=2).view(B, N, N, 2 * out_f)
        
        e = self.leakyrelu(torch.matmul(a_input, self.a).squeeze(3))
        attention = F.softmax(e, dim=2)
        h_prime = torch.matmul(attention, Wh)
        return F.elu(h_prime)

class GNNTrafficModel(TorchModelV2, nn.Module):
    def __init__(self, obs_space, action_space, num_outputs, model_config, name):
        TorchModelV2.__init__(self, obs_space, action_space, num_outputs, model_config, name)
        nn.Module.__init__(self)

        # 1. GAT KISMI: Yerel Graf İşleme (Ajanın kendi + 2 komşusu)
        # Obs: [v, w, h, n1_v, n1_w?, n2_v, n2_w?] -> Şu an 5 boyutlu (v, w, h, n1_v, n2_v)
        self.gat = GraphAttentionLayer(in_features=3, out_features=16)
        
        # 2. MLP KISMI: Eski modelle uyumlu olması için [256, 256, 256] yapısında
        # Giriş: GAT'tan gelen 16 (self node)
        self.fc_layers = nn.Sequential(
            nn.Linear(16, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU()
        )
        
        # Policy ve Value Kafaları
        self.action_head = nn.Linear(256, num_outputs)
        self.value_head = nn.Linear(256, 1)
        
        self._last_value = None

    @override(TorchModelV2)
    def forward(self, input_dict, state, seq_lens):
        obs = input_dict["obs"] # [Batch, 5] -> (v, w, h, n1_v, n2_v)
        B = obs.shape[0]
        
        # Graf oluşturma (Her ajan için 3 düğümlü yerel graf)
        # Node 0: Self [v, w, h]
        # Node 1: N1 [n1_v, 0, 0]
        # Node 2: N2 [n2_v, 0, 0]
        nodes = torch.zeros(B, 3, 3, device=obs.device)
        nodes[:, 0, :] = obs[:, 0:3]
        nodes[:, 1, 0] = obs[:, 3]
        nodes[:, 2, 0] = obs[:, 4]
        
        # Adjacency (Herkes kendine ve ana ajana bağlı)
        adj = torch.ones(B, 3, 3, device=obs.device)
        
        # GAT katmanından geçiş
        g_out = self.gat(nodes, adj) # [B, 3, 16]
        self_feat = g_out[:, 0, :]   # Sadece ana ajanın (node 0) güncellenmiş bilgisini al
        
        # MLP katmanlarından geçiş
        feat = self.fc_layers(self_feat)
        
        logits = self.action_head(feat)
        self._last_value = self.value_head(feat)
        
        return logits, state

    @override(TorchModelV2)
    def value_function(self):
        return self._last_value.squeeze(1)
