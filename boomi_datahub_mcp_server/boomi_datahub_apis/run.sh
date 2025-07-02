
#!/bin/zsh

##########
#####  

    ## Note: Before running this script, 
    ## the Conda env must have been created via bootstrap.sh:

#####
##########


# Activate the conda environment
source /opt/anaconda3/bin/activate env_MCPServer_DataHub 


# Validate if the environment is activated
if conda info --envs | grep -q "env_MCPServer_DataHub"; then
    echo "Environment 'env_MCPServer_DataHub' activated successfully."
    # Execute commands on virtual environment:

    ## Let's invoke the "test_boomi_datahub_client.py" python code:
    python test_boomi_datahub_client.py

    ### AND IT WORKS!!!!

else
    echo "Failed to activate the 'env_MCPServer_DataHub' environment."
fi


