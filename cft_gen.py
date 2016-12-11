#!/usr/bin/python
import argparse
import boto3
import re

from troposphere import Template
from troposphere import ec2, rds


# Make sure VPC_ID is specific to your aws account.
VPC_ID = 'vpc-e3b66484'

cft = Template()
cft.add_description("EC2 and RDS instance in existing VPC")

cft_client = boto3.client('cloudformation')
resource = boto3.resource('ec2')


def create_sec_grp(ports):
    """This generates a security group with the provided ports"""

    sec_grp = resource.create_security_group(GroupName='OpenPort80443ToItself',
                                             Description='Open Port 80 & 443',
                                             VpcId=VPC_ID)
    ip_permissions = [{'IpProtocol': '-1',
                       'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]

    sec_grp.revoke_egress(IpPermissions=ip_permissions)
    for port in ports:
        ip_permissions = [{'IpProtocol': 'tcp',
                           'FromPort': port,
                           'ToPort': port,
                           'IpRanges': [{'CidrIp': '127.0.0.1/32'}]}]
        sec_grp.authorize_egress(IpPermissions=ip_permissions)
        sec_grp.authorize_ingress(IpPermissions=ip_permissions)

    return sec_grp.id


def generate_ec2_instance(instance_type, security_grp_id):
    """This generates the CF template for the ec2 instance"""

    cft.add_resource(ec2.Instance("ec2instance",
                                  ImageId="ami-01f05461",
                                  InstanceType=instance_type,
                                  SecurityGroupIds=[security_grp_id]))


def generate_rds_instance(db_name, db_class, db_size,
                          db_username, db_password):
    """This generates the CF template portion for the  RDS instance"""

    cft.add_resource(rds.DBInstance("rdsinstance",
                                    Engine="MySQL",
                                    DBName=db_name,
                                    AllocatedStorage=db_size,
                                    DBInstanceClass=db_class,
                                    MasterUsername=db_username,
                                    MasterUserPassword=db_password,
                                    StorageEncrypted="True",))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', type=str, default='cft.json')
    parser.add_argument('--dbname', required=True, type=str, default='dbname')
    parser.add_argument('--dbsize', required=True, type=int, default=5)
    parser.add_argument('--ec2_ports', action='append', type=int)
    parser.add_argument('--dryrun', type=int, default=0)

    parser.add_argument('--rdsclass', required=True, type=str,
                        default='db.m3.medium')
    parser.add_argument('--rdsusername', required=True, type=str,
                        default='admin')
    parser.add_argument('--rdspassword', required=True, type=str,
                        default='password')
    parser.add_argument('--instance_type', required=True, type=str,
                        default='t2.micro')
    args = parser.parse_args()

    sec_grps = []
    if not args.dryrun:
        security_grp_id = create_sec_grp(args.ec2_ports)
        sec_grps = resource.security_groups.iterator()

    pttrn = re.compile('OpenPort80443ToItself*')
    match = [x.group_id for x in sec_grps if pttrn.match(x.group_name)]

    security_grp_id = match[0] if match else 'NoSecGroupMatch-Or-NotDefined'

    generate_ec2_instance(args.instance_type, security_grp_id)
    generate_rds_instance(args.dbname, args.rdsclass, args.dbsize,
                          args.rdsusername, args.rdspassword)

    if args.filename:
        with open(args.filename, 'w') as outfile:
            outfile.write(cft.to_json())
    else:
        print (cft.to_json())

    if not args.dryrun:
        try:
            cft_client.create_stack(StackName='UbuntuAndMysql',
                                    TemplateBody=cft.to_json())
        except Exception as e:
            raise e
