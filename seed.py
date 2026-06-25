"""
Database Seeder
Creates default admin accounts and sample complaints
"""
from pymongo import MongoClient
from dotenv import load_dotenv
import bcrypt
import os
from datetime import datetime, timedelta

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db     = client['civictrack']

def seed():
    print('\n🌱 Seeding database...\n')

    # Delete existing seed users
    db.users.delete_many({'email': {'$in': ['superadmin@civic.in','admin@civic.in','officer1@civic.in','officer2@civic.in']}})

    def hash_pw(pw):
        return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())

    # Create users
    users = db.users.insert_many([
        {'name':'Super Admin',       'email':'superadmin@civic.in', 'password':hash_pw('admin123'),   'role':'super_admin',   'phone':'9999999999', 'isActive':True, 'createdAt':datetime.utcnow()},
        {'name':'Municipal Admin',   'email':'admin@civic.in',      'password':hash_pw('admin123'),   'role':'admin',         'phone':'8888888888', 'isActive':True, 'createdAt':datetime.utcnow()},
        {'name':'Ravi Kumar',        'email':'officer1@civic.in',   'password':hash_pw('officer123'), 'role':'field_officer', 'phone':'7777777777', 'ward':'Ward 2', 'department':'Roads & Infrastructure', 'isActive':True, 'createdAt':datetime.utcnow()},
        {'name':'Priya Sharma',      'email':'officer2@civic.in',   'password':hash_pw('officer123'), 'role':'field_officer', 'phone':'6666666666', 'ward':'Ward 3', 'department':'Sanitation & Waste Mgmt', 'isActive':True, 'createdAt':datetime.utcnow()},
    ])

    sa_id = users.inserted_ids[0]
    ad_id = users.inserted_ids[1]
    o1_id = users.inserted_ids[2]
    o2_id = users.inserted_ids[3]

    # Delete existing complaints
    db.complaints.delete_many({})

    # Create sample complaints
    db.complaints.insert_many([
        {
            'trackingId':'CVT-001001-1001','title':'Large pothole on MG Road',
            'description':'Dangerous pothole near City Bank causing accidents daily',
            'issueType':'pothole','priority':'high','status':'in_progress',
            'urgencyScore':75,'citizen':sa_id,'assignedOfficer':o1_id,
            'department':'Roads & Infrastructure',
            'aiClassification':{'predictedType':'pothole','confidence':0.87,'method':'Python OpenCV + NumPy'},
            'location':{'address':'MG Road, Ward 2','ward':'Ward 2','coordinates':{'lat':16.5074,'lng':80.4989}},
            'upvotes':[],'upvoteCount':15,'photos':[],'timeline':[
                {'status':'submitted','message':'Submitted','updatedBy':sa_id,'updatedAt':datetime.utcnow()-timedelta(days=3)},
                {'status':'assigned','message':'Assigned to Ravi Kumar','updatedBy':ad_id,'updatedAt':datetime.utcnow()-timedelta(days=2)},
                {'status':'in_progress','message':'Repair crew dispatched','updatedBy':o1_id,'updatedAt':datetime.utcnow()-timedelta(days=1)},
            ],'createdAt':datetime.utcnow()-timedelta(days=3),'updatedAt':datetime.utcnow()
        },
        {
            'trackingId':'CVT-001002-1002','title':'Garbage not collected for 5 days',
            'description':'Garbage overflowing near market creating health hazard',
            'issueType':'garbage','priority':'critical','status':'assigned',
            'urgencyScore':90,'citizen':sa_id,'assignedOfficer':o2_id,
            'department':'Sanitation & Waste Mgmt',
            'aiClassification':{'predictedType':'garbage','confidence':0.82,'method':'Python OpenCV + NumPy'},
            'location':{'address':'Market Street, Ward 3','ward':'Ward 3','coordinates':{'lat':16.5182,'lng':80.5151}},
            'upvotes':[],'upvoteCount':32,'photos':[],'timeline':[
                {'status':'submitted','message':'Submitted','updatedBy':sa_id,'updatedAt':datetime.utcnow()-timedelta(days=2)},
                {'status':'assigned','message':'Assigned to Priya Sharma','updatedBy':ad_id,'updatedAt':datetime.utcnow()-timedelta(days=1)},
            ],'createdAt':datetime.utcnow()-timedelta(days=2),'updatedAt':datetime.utcnow()
        },
        {
            'trackingId':'CVT-001003-1003','title':'Streetlight not working on Colony Road',
            'description':'3 streetlights out making road dangerous at night',
            'issueType':'streetlight','priority':'medium','status':'resolved',
            'urgencyScore':45,'citizen':sa_id,'assignedOfficer':None,
            'department':'Electricity & Lighting',
            'aiClassification':{'predictedType':'streetlight','confidence':0.79,'method':'Python OpenCV + NumPy'},
            'location':{'address':'Colony Road, Ward 1','ward':'Ward 1','coordinates':{'lat':16.4939,'lng':80.5022}},
            'upvotes':[],'upvoteCount':8,'photos':[],'resolutionTimeHours':48,
            'resolvedAt':datetime.utcnow()-timedelta(days=1),'resolutionNote':'All 3 streetlights repaired and tested',
            'timeline':[
                {'status':'submitted','message':'Submitted','updatedBy':sa_id,'updatedAt':datetime.utcnow()-timedelta(days=4)},
                {'status':'resolved','message':'All lights repaired','updatedBy':ad_id,'updatedAt':datetime.utcnow()-timedelta(days=1)},
            ],'createdAt':datetime.utcnow()-timedelta(days=4),'updatedAt':datetime.utcnow()
        },
        {
            'trackingId':'CVT-001004-1004','title':'Drainage overflow near school',
            'description':'Drainage water on road near government school — health hazard',
            'issueType':'drainage','priority':'critical','status':'submitted',
            'urgencyScore':95,'citizen':sa_id,'assignedOfficer':None,
            'department':'Water & Drainage Dept',
            'aiClassification':{'predictedType':'drainage','confidence':0.91,'method':'Python OpenCV + NumPy'},
            'location':{'address':'School Road, Ward 4','ward':'Ward 4','coordinates':{'lat':16.5312,'lng':80.5089}},
            'upvotes':[],'upvoteCount':45,'photos':[],'timeline':[
                {'status':'submitted','message':'Submitted','updatedBy':sa_id,'updatedAt':datetime.utcnow()},
            ],'createdAt':datetime.utcnow()-timedelta(hours=5),'updatedAt':datetime.utcnow()
        },
        {
            'trackingId':'CVT-001005-1005','title':'Water supply disrupted for 2 days',
            'description':'No water supply in Sector 5 for 2 days — families suffering',
            'issueType':'water_supply','priority':'critical','status':'acknowledged',
            'urgencyScore':100,'citizen':sa_id,'assignedOfficer':None,
            'department':'Water Supply Dept',
            'aiClassification':{'predictedType':'water_supply','confidence':0.88,'method':'Python OpenCV + NumPy'},
            'location':{'address':'Sector 5, Ward 5','ward':'Ward 5','coordinates':{'lat':16.5421,'lng':80.4876}},
            'upvotes':[],'upvoteCount':60,'photos':[],'timeline':[
                {'status':'submitted','message':'Submitted','updatedBy':sa_id,'updatedAt':datetime.utcnow()-timedelta(hours=10)},
                {'status':'acknowledged','message':'Water board notified urgently','updatedBy':ad_id,'updatedAt':datetime.utcnow()-timedelta(hours=8)},
            ],'createdAt':datetime.utcnow()-timedelta(hours=10),'updatedAt':datetime.utcnow()
        },
    ])

    print('━'*50)
    print('✅ DATABASE SEEDED SUCCESSFULLY!')
    print('━'*50)
    print('  Super Admin  → superadmin@civic.in / admin123')
    print('  Admin        → admin@civic.in / admin123')
    print('  Officer 1    → officer1@civic.in / officer123')
    print('  Officer 2    → officer2@civic.in / officer123')
    print('━'*50)
    print('  5 sample complaints created')
    print('━'*50)
    client.close()

if __name__ == '__main__':
    seed()
