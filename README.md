# CFT Generator and Stack Wrapper

The AWS Python Wrapper Generates a CF Template and Spins the Stack with the CFT.
Make sure that you setup your virual enviroment and install the dependencies. 
Also make sure that then VPC_ID parameter is given a value that exists in your console.
  
    1. pip install requirements.txt
To execute the script you would need to run the following command. Default values have
been provided to the options if the user does not choose to provide values. 

If you do not provide filename the output will be displayed on stdout and will not save it
to the file. There is a dryrun flag as well which will generate the CFT for you.
       
    2. python cft_gen.py --rdsclass=db.m3.medium --rdsusername=admin --rdspassword=password
       --dbname=Test --dbsize=5 --instance_type=t2.micro --ec2_ports 80 --ec2_ports 443
       --dryrun=0 --filename=cft.json
