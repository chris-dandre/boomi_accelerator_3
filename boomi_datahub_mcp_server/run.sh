
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

    ## 1. Pre-requisites:
    # Make sure that "boomi_datahub_client" has set the .env properties accordingly"
        # BOOMI_USERNAME=your_username
        # BOOMI_PASSWORD=your_password
        # BOOMI_ACCOUNT_ID=your_account_id
        # BOOMI_BASE_URL=https://api.boomi.com  # optional

    ## 2. Run the "boomi_mcp_server":
    python boomi_mcp_server/boomi_datahub_mcp_server.py

    ## 3. In a separate terminal, activate virtual
    ## environment (i.e. conda activate env_MCPServer_DataHub) and Call the "boomi_mcp_client":
    python boomi_mcp_server/boomi_datahub_mcp_client.py

    ### AND IT WORKS!!!!

else
    echo "Failed to activate the 'env_MCPServer_DataHub' environment."
fi


