"""GRU-D: Gated Recurrent Unit with Decay for Irregular Time-Series

Cutting-edge temporal model that handles missing values and irregular sampling
better than traditional LSTM. Published in Scientific Reports 2018.

Key innovations:
- Time decay mechanism for missing data
- Input decay for feature values
- Masking mechanism for observed vs missing
- Superior performance on ICU datasets (5-10% AUC improvement over LSTM)
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Tuple, Optional


class GRUDCell(nn.Module):
    """GRU-D Cell with decay mechanism"""
    
    def __init__(self, input_size: int, hidden_size: int):
        super(GRUDCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        
        # Standard GRU gates
        self.weight_ih = nn.Linear(input_size, 3 * hidden_size)
        self.weight_hh = nn.Linear(hidden_size, 3 * hidden_size)
        
        # Decay parameters
        self.decay_h = nn.Linear(input_size, hidden_size)
        self.decay_x = nn.Linear(input_size, input_size)
        
    def forward(
        self,
        x: torch.Tensor,
        h: torch.Tensor,
        mask: torch.Tensor,
        delta: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass with decay
        
        Args:
            x: Input features [batch, input_size]
            h: Hidden state [batch, hidden_size]
            mask: Observation mask [batch, input_size] (1=observed, 0=missing)
            delta: Time since last observation [batch, input_size]
            
        Returns:
            Tuple of (output, new_hidden_state)
        """
        # Compute decay factors
        gamma_h = torch.exp(-torch.relu(self.decay_h(delta)))
        gamma_x = torch.exp(-torch.relu(self.decay_x(delta)))
        
        # Apply decay to hidden state
        h = gamma_h * h
        
        # Apply decay to input and handle missing values
        x_decayed = gamma_x * x
        x_input = mask * x + (1 - mask) * x_decayed
        
        # Standard GRU computation
        gi = self.weight_ih(x_input)
        gh = self.weight_hh(h)
        i_r, i_u, i_n = gi.chunk(3, 1)
        h_r, h_u, h_n = gh.chunk(3, 1)
        
        resetgate = torch.sigmoid(i_r + h_r)
        updategate = torch.sigmoid(i_u + h_u)
        newgate = torch.tanh(i_n + resetgate * h_n)
        
        hy = (1 - updategate) * newgate + updategate * h
        
        return hy, hy


class GRUD(nn.Module):
    """GRU-D Model for ICU Time-Series Prediction"""
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_layers: int = 2,
        dropout: float = 0.3,
        output_size: int = 1
    ):
        super(GRUD, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # Stack of GRU-D cells
        self.cells = nn.ModuleList([
            GRUDCell(input_size if i == 0 else hidden_size, hidden_size)
            for i in range(num_layers)
        ])
        
        self.dropout = nn.Dropout(dropout)
        
        # Output layer
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor,
        delta: torch.Tensor,
        h0: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through GRU-D
        
        Args:
            x: Input sequence [batch, seq_len, input_size]
            mask: Observation mask [batch, seq_len, input_size]
            delta: Time deltas [batch, seq_len, input_size]
            h0: Initial hidden state [num_layers, batch, hidden_size]
            
        Returns:
            Tuple of (output, final_hidden_state)
        """
        batch_size, seq_len, _ = x.size()
        
        # Initialize hidden state
        if h0 is None:
            h = [torch.zeros(batch_size, self.hidden_size, device=x.device)
                 for _ in range(self.num_layers)]
        else:
            h = [h0[i] for i in range(self.num_layers)]
        
        outputs = []
        
        # Process sequence
        for t in range(seq_len):
            x_t = x[:, t, :]
            mask_t = mask[:, t, :]
            delta_t = delta[:, t, :]
            
            # Pass through layers
            for i, cell in enumerate(self.cells):
                if i == 0:
                    h[i], _ = cell(x_t, h[i], mask_t, delta_t)
                else:
                    h[i], _ = cell(h[i-1], h[i], mask_t, delta_t)
                    h[i] = self.dropout(h[i])
            
            outputs.append(h[-1])
        
        # Stack outputs
        output_seq = torch.stack(outputs, dim=1)  # [batch, seq_len, hidden_size]
        
        # Use last output for prediction
        final_output = self.fc(output_seq[:, -1, :])
        
        return final_output, torch.stack(h)


class GRUD_Sepsis_Predictor(nn.Module):
    """GRU-D based Sepsis Prediction Model
    
    Target: AUC > 0.85 on test set
    """
    
    def __init__(
        self,
        input_size: int = 20,  # Number of clinical features
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3
    ):
        super(GRUD_Sepsis_Predictor, self).__init__()
        
        self.grud = GRUD(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            output_size=64  # Intermediate representation
        )
        
        # Classification head with attention
        self.attention = nn.Linear(64, 1)
        self.classifier = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor,
        delta: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Predict sepsis probability
        
        Args:
            x: Time-series features [batch, seq_len, input_size]
            mask: Observation mask [batch, seq_len, input_size]
            delta: Time deltas [batch, seq_len, input_size]
            
        Returns:
            Tuple of (probability, attention_weights)
        """
        # Get GRU-D representation
        representation, _ = self.grud(x, mask, delta)
        
        # Apply attention (for interpretability)
        attention_weights = torch.softmax(self.attention(representation), dim=0)
        
        # Classify
        probability = self.classifier(representation)
        
        return probability, attention_weights


class GRUD_MultiTask_Predictor(nn.Module):
    """Multi-task GRU-D for multiple clinical predictions
    
    Predicts:
    - Sepsis risk
    - Mortality risk
    - Organ failure risk
    - Length of stay
    """
    
    def __init__(
        self,
        input_size: int = 20,
        hidden_size: int = 128,
        num_layers: int = 2
    ):
        super(GRUD_MultiTask_Predictor, self).__init__()
        
        # Shared GRU-D backbone
        self.backbone = GRUD(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=0.3,
            output_size=128
        )
        
        # Task-specific heads
        self.sepsis_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
        self.mortality_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
        self.organ_failure_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 6),  # 6 organs
            nn.Sigmoid()
        )
        
        self.los_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor,
        delta: torch.Tensor
    ) -> dict:
        """Multi-task prediction
        
        Returns:
            Dictionary with all predictions
        """
        # Shared representation
        representation, _ = self.backbone(x, mask, delta)
        
        return {
            'sepsis_prob': self.sepsis_head(representation),
            'mortality_prob': self.mortality_head(representation),
            'organ_failure_prob': self.organ_failure_head(representation),
            'predicted_los': self.los_head(representation)
        }
