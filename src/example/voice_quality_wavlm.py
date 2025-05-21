import torch
import sys, os, pdb
import torch.nn as nn
import argparse, logging
import torch.nn.functional as F

from pathlib import Path


sys.path.append(os.path.join(str(Path(os.path.realpath(__file__)).parents[1])))
sys.path.append(os.path.join(str(Path(os.path.realpath(__file__)).parents[1]), 'model', 'voice_quality'))

from wavlm_voice_quality import WavLMWrapper


# define logging console
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-3s ==> %(message)s', 
    level=logging.INFO, 
    datefmt='%Y-%m-%d %H:%M:%S'
)

os.environ["MKL_NUM_THREADS"] = "1" 
os.environ["NUMEXPR_NUM_THREADS"] = "1" 
os.environ["OMP_NUM_THREADS"] = "1" 


if __name__ == '__main__':

    label_list = [
        'shrill', 'nasal', 'deep',  # Pitch
        'silky', 'husky', 'raspy', 'guttural', 'vocal-fry', # Texture
        'booming', 'authoritative', 'loud', 'hushed', 'soft', # Volume
        'crisp', 'slurred', 'lisp', 'stammering', # Clarity
        'singsong', 'pitchy', 'flowing', 'monotone', 'staccato', 'punctuated', 'enunciated',  'hesitant', # Rhythm
    ]
    
    # Find device
    device = torch.device("cuda") if torch.cuda.is_available() else "cpu"
    if torch.cuda.is_available(): print('GPU available, use GPU')

    # Define the model
    # Note that ensemble yields the better performance than the single model
    model_path = "model"
    # Define the model wrapper
    wavlm_model = WavLMWrapper(
        pretrain_model="wavlm_large", 
        hidden_dim=256,
        finetune_method="lora",
        lora_rank=16,
        freeze_params=True,
        use_conv_output=True,
        percept="complete"
    ).to(device)
    
    wavlm_model.load_state_dict(torch.load(os.path.join(model_path, f"wavlm_voice_quality.pt"), weights_only=True), strict=False)
    wavlm_model.load_state_dict(torch.load(os.path.join(model_path, f"wavlm_voice_quality_lora.pt")), strict=False)
    wavlm_model.eval()

    # audio sample frequency is set to 16kHz
    data = torch.zeros([1, 16000]).to(device)
    wavlm_logits = wavlm_model(data, return_feature=False)
    wavlm_prob = nn.Sigmoid()(torch.tensor(wavlm_logits))
    
    # In practice, a larger threshold would remove some noise, but it is best to aggregate prediction per speaker
    threshold = 0.5
    predictions = (wavlm_prob > threshold).int().detach().cpu().numpy()[0].tolist()
    print(wavlm_prob.shape)

