
#!/bin/zsh

# Activate the conda environment
source /opt/anaconda3/bin/activate env_MCPServer_DataHub 


# Validate if the environment is activated
if conda info --envs | grep -q "env_MCPServer_DataHub"; then

    echo "Environment 'env_MCPServer_DataHub' already exists.. No need to re-create."

else
    echo "env_MCPServer_DataHub does not exist. Creating virtual environment now..."
    conda env list
    conda env create -f env_MCPServer_DataHub.yml
    conda env list
    conda activate env_MCPServer_DataHub
    conda deactivate    
    #conda env update --file env_MCPServer_DataHub.yml  --prune
fi