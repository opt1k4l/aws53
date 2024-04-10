import boto3
import subprocess
import csv

# Initialize a Route53 client
client = boto3.client('route53')

# Function to handle pagination and list all hosted zones
def list_hosted_zones():
    paginator = client.get_paginator('list_hosted_zones')
    hosted_zones = []
    for page in paginator.paginate():
        hosted_zones.extend(page['HostedZones'])
    return hosted_zones

# Function to get nameservers for a domain from Route 53
def get_nameservers_from_route53(hosted_zone_id):
    response = client.get_hosted_zone(Id=hosted_zone_id)
    nameservers = response['DelegationSet']['NameServers']
    return nameservers

# Function to check domain's actual nameservers (via system's 'dig' command or similar)
def get_actual_nameservers(domain_name):
    try:
        # Using 'dig' command; you might need to adapt this depending on your OS
        result = subprocess.run(['dig', '+short', 'NS', domain_name], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.splitlines()
        else:
            return None
    except Exception as e:
        print(f"Error fetching actual nameservers for {domain_name}: {e}")
        return None

# Function to write results to CSV
def write_to_csv(rows):
    with open('domain_nameservers_status.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Domain Name", "Using Route 53 Nameservers"])
        writer.writerows(rows)

def main():
    zones = list_hosted_zones()
    rows = []
    for zone in zones:
        domain_name = zone['Name']
        hosted_zone_id = zone['Id']

        route53_ns = get_nameservers_from_route53(hosted_zone_id)
        actual_ns = get_actual_nameservers(domain_name)

        if actual_ns:
            # Normalize to ensure comparison works irrespective of trailing periods and case
            route53_ns_normalized = {ns.lower().rstrip('.') for ns in route53_ns}
            actual_ns_normalized = {ns.lower().rstrip('.') for ns in actual_ns}

            if route53_ns_normalized == actual_ns_normalized:
                rows.append([domain_name, "Yes"])
            else:
                rows.append([domain_name, "No"])
        else:
            rows.append([domain_name, "Unknown"])

    write_to_csv(rows)
    print("CSV file 'domain_nameservers_status.csv' has been created.")

if __name__ == "__main__":
    main()
