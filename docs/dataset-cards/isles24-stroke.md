---
license: cc-by-nc-sa-4.0
task_categories:
  - image-segmentation
tags:
  - medical
  - neuroimaging
  - stroke
  - CT
  - MRI
  - perfusion
  - ISLES
  - BIDS
size_categories:
  - n<1K
---

# ISLES'24 Stroke Training Dataset

Multi-center longitudinal multimodal acute ischemic stroke training dataset from the ISLES'24 Challenge.

## Dataset Description

- **Source:** [Zenodo Record 17652035](https://zenodo.org/records/17652035) (v7, November 2025)
- **Challenge:** [ISLES 2024](https://isles-24.grand-challenge.org/)
- **Paper:** [Riedel et al., arXiv:2408.11142](https://arxiv.org/abs/2408.11142)
- **License:** CC BY-NC-SA 4.0
- **Size:** 99 GB (compressed)

## Overview

149 acute ischemic stroke training cases with:
- **Admission imaging (ses-0001):** Non-contrast CT, CT angiography, 4D CT perfusion
- **Follow-up imaging (ses-0002):** Post-treatment MRI (DWI, ADC)
- **Clinical data:** Demographics, patient history, admission NIHSS, 3-month mRS outcomes
- **Annotations:** Infarct masks, large vessel occlusion masks, Circle of Willis anatomy

> **Note:** The ISLES'24 paper describes a training set of 150 cases; the Zenodo v7 training archive contains 149 publicly released subjects.

## Dataset Structure

### Imaging Modalities

| Session | Modality | Description |
|---------|----------|-------------|
| ses-0001 (Acute) | `ncct` | Non-contrast CT |
| ses-0001 (Acute) | `cta` | CT Angiography |
| ses-0001 (Acute) | `ctp` | 4D CT Perfusion time series |
| ses-0001 (Acute) | `tmax` | Time-to-maximum perfusion map |
| ses-0001 (Acute) | `mtt` | Mean transit time map |
| ses-0001 (Acute) | `cbf` | Cerebral blood flow map |
| ses-0001 (Acute) | `cbv` | Cerebral blood volume map |
| ses-0002 (Follow-up) | `dwi` | Diffusion-weighted MRI |
| ses-0002 (Follow-up) | `adc` | Apparent diffusion coefficient |

### Derivative Masks

| Mask | Description |
|------|-------------|
| `lesion_mask` | Binary infarct segmentation (from follow-up MRI) |
| `lvo_mask` | Large vessel occlusion mask (from CTA) |
| `cow_mask` | Circle of Willis anatomy (multi-label, auto-generated from CTA) |

### Clinical Variables

Clinical variables are sourced from the BIDS `phenotype/` tables:

| Variable | Description |
|----------|-------------|
| `nihss_admission` | NIH Stroke Scale score at admission |
| `mrs_3month` | Modified Rankin Scale at 3 months |
| Demographics | Age, sex, patient history |

## Usage

```python
from datasets import load_dataset

ds = load_dataset("hugging-science/isles24-stroke", split="train")

# Access a subject
example = ds[0]
print(example["subject_id"])      # "sub-strokecase0001"
print(example["ncct"])            # Non-contrast CT array
print(example["dwi"])             # Diffusion-weighted MRI
print(example["lesion_mask"])     # Ground truth segmentation
print(example["nihss_admission"]) # Stroke severity score
```

## Data Organization

The source data follows BIDS structure. Filenames shown are illustrative and follow the BIDS naming pattern used in the archive:

```
raw_data/
└── sub-strokecase0001/
    └── ses-0001/
        ├── sub-strokecase0001_ses-0001_ncct.nii.gz
        ├── sub-strokecase0001_ses-0001_cta.nii.gz
        ├── sub-strokecase0001_ses-0001_ctp.nii.gz
        └── perfusion-maps/
            ├── sub-strokecase0001_ses-0001_tmax.nii.gz
            ├── sub-strokecase0001_ses-0001_mtt.nii.gz
            ├── sub-strokecase0001_ses-0001_cbf.nii.gz
            └── sub-strokecase0001_ses-0001_cbv.nii.gz

derivatives/
└── sub-strokecase0001/
    ├── ses-0001/
    │   ├── perfusion-maps/
    │   │   ├── sub-strokecase0001_ses-0001_space-ncct_tmax.nii.gz
    │   │   ├── sub-strokecase0001_ses-0001_space-ncct_mtt.nii.gz
    │   │   ├── sub-strokecase0001_ses-0001_space-ncct_cbf.nii.gz
    │   │   └── sub-strokecase0001_ses-0001_space-ncct_cbv.nii.gz
    │   ├── sub-strokecase0001_ses-0001_space-ncct_cta.nii.gz
    │   ├── sub-strokecase0001_ses-0001_space-ncct_ctp.nii.gz
    │   ├── sub-strokecase0001_ses-0001_space-ncct_lvo-msk.nii.gz
    │   └── sub-strokecase0001_ses-0001_space-ncct_cow-msk.nii.gz
    └── ses-0002/
        ├── sub-strokecase0001_ses-02_space-ncct_dwi.nii.gz
        ├── sub-strokecase0001_ses-02_space-ncct_adc.nii.gz
        └── sub-strokecase0001_ses-02_space-ncct_lesion-msk.nii.gz

phenotype/
├── ses-0001/
│   └── sub-strokecase0001_ses-0001_demographic_baseline.csv
└── ses-0002/
    └── sub-strokecase0001_ses-0001_outcome.csv
```

## Citation

When using this dataset, please cite:

```bibtex
@article{riedel2024isles,
  title={ISLES'24 -- A Real-World Longitudinal Multimodal Stroke Dataset},
  author={Riedel, Evamaria Olga and de la Rosa, Ezequiel and Baran, The Anh and
          Hernandez Petzsche, Moritz and Baazaoui, Hakim and Yang, Kaiyuan and
          Musio, Fabio Antonio and Huang, Houjing and Robben, David and
          Seia, Joaquin Oscar and Wiest, Roland and Reyes, Mauricio and
          Su, Ruisheng and Zimmer, Claus and Boeckh-Behrens, Tobias and
          Berndt, Maria and Menze, Bjoern and Rueckert, Daniel and
          Wiestler, Benedikt and Wegener, Susanne and Kirschke, Jan Stefan},
  journal={arXiv preprint arXiv:2408.11142},
  year={2024}
}

@article{delarosa2024isles,
  title={ISLES'24: Final Infarct Prediction with Multimodal Imaging and Clinical Data. Where Do We Stand?},
  author={de la Rosa, Ezequiel and Su, Ruisheng and Reyes, Mauricio and
          Wiest, Roland and Riedel, Evamaria Olga and Kofler, Florian and
          others and Menze, Bjoern},
  journal={arXiv preprint arXiv:2408.10966},
  year={2024}
}
```

If using Circle of Willis masks, also cite:

```bibtex
@article{yang2023benchmarking,
  title={Benchmarking the CoW with the TopCoW Challenge: Topology-Aware Anatomical
         Segmentation of the Circle of Willis for CTA and MRA},
  author={Yang, Kaiyuan and Musio, Fabio and Ma, Yue and Juchler, Norman and
          Paetzold, Johannes C and Al-Maskari, Rami and others and Menze, Bjoern},
  journal={arXiv preprint arXiv:2312.17670},
  year={2023}
}
```

## Related Resources

- [ISLES 2024 Challenge](https://isles-24.grand-challenge.org/)
- [Zenodo Dataset (DOI: 10.5281/zenodo.17652035)](https://doi.org/10.5281/zenodo.17652035)
- [Dataset Paper (arXiv:2408.11142)](https://arxiv.org/abs/2408.11142)
- [Challenge Paper (arXiv:2408.10966)](https://arxiv.org/abs/2408.10966)
