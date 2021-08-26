# epix-hr-dev

# Before you clone the GIT repository

1) Create a github account:
> https://github.com/

2) On the Linux machine that you will clone the github from, generate a SSH key (if not already done)
> https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/

3) Add a new SSH key to your GitHub account
> https://help.github.com/articles/adding-a-new-ssh-key-to-your-github-account/

4) Setup for large filesystems on github (one-time operation)
> $ git lfs install

# Clone the GIT repository
``` $ git clone --recursive git@github.com:slaclab/epix-hr-dev```


# Prgrame camera mcs file

1) go to folder
cd epix-hr-single-10k/software

2) source the environment
source setup_env_slac.sh

3) run script (substitute "EpixHr10kT-0x03010000-20210823153944-ddoering-20f1553.mcs" with your file
python ./scripts/updateEpixHr  --mcs   ../firmware/targets/EpixHr10kT/images/EpixHr10kT-0x03010000-20210823153944-ddoering-20f1553.mcs --lane 0