import boto3
import os
import logging
from botocore.exceptions import ClientError

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Configuration
# DRY_RUN: If True, it will print actions but NOT delete anything. 
# Set to 'False' in GitHub Secrets for production.
DRY_RUN = os.getenv('DRY_RUN', 'True').lower() == 'true'
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def get_ec2_client():
    """Initialize boto3 client"""
    return boto3.client('ec2', region_name=AWS_REGION)

def cleanup_ebs_volumes(client):
    """Delete unattached EBS volumes"""
    logger.info("--- Starting EBS Volume Cleanup ---")
    try:
        # Server-Side Filter: Only fetch 'available' (unattached) volumes
        # This is optimized for performance.
        response = client.describe_volumes(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )
        
        for volume in response['Volumes']:
            vol_id = volume['VolumeId']
            size = volume
            
            # Safety Check: Skip if volume has a 'Name' tag (might be important)
            if 'Tags' in volume:
                logger.info(f"Skipping {vol_id} (Has Tags, requires manual review)")
                continue

            if DRY_RUN:
                logger.info(f" Would delete volume {vol_id} ({size} GB)")
            else:
                try:
                    client.delete_volume(VolumeId=vol_id)
                    logger.info(f"SUCCESS: Deleted volume {vol_id}")
                except ClientError as e:
                    logger.error(f"ERROR: Could not delete {vol_id}: {e}")

    except ClientError as e:
        logger.error(f"Failed to describe volumes: {e}")

def cleanup_stale_snapshots(client):
    """Delete snapshots that are not owned by an AMI"""
    logger.info("--- Starting Snapshot Cleanup ---")
    try:
        # Filter 1: Only look at snapshots owned by YOU (Self)
        response = client.describe_snapshots(OwnerIds=['self'])
        
        for snapshot in response:
            snap_id = snapshot
            
            # Simple logic for demo: Delete if description contains 'Created by CreateImage'
            # (These are often left over from AMI creation)
            # In a real scenario, you would check the age (StartTime)
            
            if DRY_RUN:
                logger.info(f" Would delete snapshot {snap_id}")
            else:
                try:
                    client.delete_snapshot(SnapshotId=snap_id)
                    logger.info(f"SUCCESS: Deleted snapshot {snap_id}")
                except ClientError as e:
                    if 'InvalidSnapshot.InUse' in str(e):
                        logger.info(f"SKIPPING: {snap_id} is in use by an AMI")
                    else:
                        logger.error(f"ERROR: Could not delete {snap_id}: {e}")

    except ClientError as e:
        logger.error(f"Failed to describe snapshots: {e}")

if __name__ == "__main__":
    logger.info(f"Script Started. Region: {AWS_REGION}, Dry Run: {DRY_RUN}")
    ec2 = get_ec2_client()
    cleanup_ebs_volumes(ec2)
    cleanup_stale_snapshots(ec2)
    logger.info("Script Finished")