from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

class Database:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['skill_credentialing']

        # Collections
        self.users = self.db['users']
        self.skills = self.db['skills']
        self.credentials = self.db['credentials']
        self.blockchain = self.db['blockchain']

        # Create indexes
        try:
            self.users.create_index('email', unique=True)
            self.users.create_index('username', unique=True)
        except:
            pass

    def get_user_by_email(self, email):
        return self.users.find_one({'email': email})

    def get_user_by_username(self, username):
        return self.users.find_one({'username': username})

    def get_user_by_id(self, user_id):
        return self.users.find_one({'_id': ObjectId(user_id)})

    def create_user(self, user_data):
        user_data['created_at'] = datetime.utcnow()
        user_data['credibility_score'] = 0
        result = self.users.insert_one(user_data)
        return result.inserted_id

    def submit_skill(self, skill_data):
        skill_data['submitted_at'] = datetime.utcnow()
        skill_data['status'] = 'pending'
        result = self.skills.insert_one(skill_data)
        return result.inserted_id

    def get_pending_skills(self):
        return list(self.skills.find({'status': 'pending'}).sort('submitted_at', -1))

    def get_student_skills(self, student_id):
        return list(self.skills.find({'student_id': student_id}).sort('submitted_at', -1))

    def get_skill_by_id(self, skill_id):
        return self.skills.find_one({'_id': ObjectId(skill_id)})

    def update_skill_status(self, skill_id, status, faculty_id, comments='', rating=3):
        self.skills.update_one(
            {'_id': ObjectId(skill_id)},
            {
                '$set': {
                    'status': status,
                    'faculty_id': faculty_id,
                    'faculty_comments': comments,
                    'rating': rating,
                    'verified_at': datetime.utcnow()
                }
            }
        )

    def add_credential(self, credential_data):
        credential_data['created_at'] = datetime.utcnow()
        result = self.credentials.insert_one(credential_data)
        return result.inserted_id

    def get_student_credentials(self, student_id):
        return list(self.credentials.find({'student_id': student_id}).sort('created_at', -1))

    def get_credential_by_hash(self, credential_hash):
        return self.credentials.find_one({'credential_hash': credential_hash})

    def add_block(self, block_data):
        result = self.blockchain.insert_one(block_data)
        return result.inserted_id

    def get_latest_block(self):
        return self.blockchain.find_one(sort=[('block_number', -1)])

    def get_all_blocks(self):
        return list(self.blockchain.find().sort('block_number', 1))

    def update_credibility_score(self, student_id, score):
        self.users.update_one(
            {'_id': ObjectId(student_id)},
            {'$set': {'credibility_score': score, 'updated_at': datetime.utcnow()}}
        )

db = Database()