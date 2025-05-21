import torch
import sys, os, pdb
import argparse, logging
import torch.nn.functional as F

from pathlib import Path


sys.path.append(os.path.join(str(Path(os.path.realpath(__file__)).parents[1])))
sys.path.append(os.path.join(str(Path(os.path.realpath(__file__)).parents[1]), 'model', 'age_sex'))

from wavlm_demographics import WavLMWrapper

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

    sex_unique_labels = ["Female", "Male"]

    # Find device
    device = torch.device("cuda") if torch.cuda.is_available() else "cpu"
    if torch.cuda.is_available(): print('GPU available, use GPU')

    # Define the model
    # Note that ensemble yields the better performance than the single model
    wavlm_model = WavLMWrapper(
        pretrain_model="wavlm_large", 
        finetune_method="lora",
        lora_rank=16,
        output_class_num=2,
        freeze_params=True, 
        use_conv_output=True,
        apply_gradient_reversal=False,
        apply_reg=True
    )

    wavlm_model = wavlm_model.from_pretrained("tiantiaf/wavlm-large-age-sex").to(device)
    # wavlm_model.eval()

    # Audio must be 16k Hz
    data = torch.zeros([1, 16000]).float().to(device)
    wavlm_age_outputs, wavlm_sex_outputs = wavlm_model(data)

    # Age is between 0-100
    age_pred = wavlm_age_outputs.detach().cpu().numpy() * 100

    sex_prob = F.softmax(wavlm_sex_outputs, dim=1)
    print(sex_unique_labels[torch.argmax(sex_prob).detach().cpu().item()])
    print(age_pred)