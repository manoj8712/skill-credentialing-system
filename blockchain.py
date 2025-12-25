import hashlib
import json
from datetime import datetime

class Blockchain:
    def __init__(self, db):
        self.db = db
        self.initialize_genesis_block()

    def initialize_genesis_block(self):
        latest_block = self.db.get_latest_block()
        if not latest_block:
            genesis_block = {
                'block_number': 0,
                'timestamp': datetime.utcnow().isoformat(),
                'data': 'Genesis Block - Skill Credentialing System',
                'previous_hash': '0',
                'hash': self.calculate_hash('0', 'Genesis Block', datetime.utcnow().isoformat())
            }
            self.db.add_block(genesis_block)

    def calculate_hash(self, previous_hash, data, timestamp):
        block_string = f"{previous_hash}{data}{timestamp}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def create_credential_hash(self, student_id, skill_name, proof_url, faculty_id):
        timestamp = datetime.utcnow().isoformat()
        credential_string = f"{student_id}{skill_name}{proof_url}{timestamp}{faculty_id}"
        return hashlib.sha256(credential_string.encode()).hexdigest()

    def add_credential_block(self, credential_data):
        latest_block = self.db.get_latest_block()
        previous_hash = latest_block['hash'] if latest_block else '0'
        block_number = latest_block['block_number'] + 1 if latest_block else 1

        timestamp = datetime.utcnow().isoformat()
        data = json.dumps(credential_data, default=str)
        block_hash = self.calculate_hash(previous_hash, data, timestamp)

        block = {
            'block_number': block_number,
            'timestamp': timestamp,
            'data': credential_data,
            'previous_hash': previous_hash,
            'hash': block_hash
        }

        self.db.add_block(block)
        return block_hash

    def verify_credential(self, credential_hash):
        credential = self.db.get_credential_by_hash(credential_hash)
        if not credential:
            return {'valid': False, 'message': 'Credential not found'}

        return {
            'valid': True,
            'message': 'Credential verified successfully',
            'details': {
                'student_id': credential['student_id'],
                'skill_name': credential['skill_name'],
                'category': credential['category'],
                'faculty_name': credential['faculty_name'],
                'credential_hash': credential['credential_hash']
            }
        }

    def verify_chain_integrity(self):
        blocks = self.db.get_all_blocks()

        if len(blocks) == 0:
            return {'valid': False, 'message': 'No blocks in chain'}

        for i in range(1, len(blocks)):
            current_block = blocks[i]
            previous_block = blocks[i-1]

            if current_block['previous_hash'] != previous_block['hash']:
                return {'valid': False, 'message': f'Chain broken at block {current_block["block_number"]}'}

        return {'valid': True, 'message': 'Blockchain integrity verified', 'total_blocks': len(blocks)}

    def calculate_credibility_score(self, student_id):
        skills = self.db.get_student_skills(student_id)

        approved = [s for s in skills if s['status'] == 'approved']
        rejected = [s for s in skills if s['status'] == 'rejected']

        verified_count = len(approved)
        rejected_count = len(rejected)

        categories = set([s.get('category', 'general') for s in approved])
        skill_diversity = len(categories)

        ratings = [s.get('rating', 3) for s in approved if 'rating' in s]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        score = (verified_count * 10) + (skill_diversity * 5) + (avg_rating * 10)
        score -= (rejected_count * 5)

        return max(0, min(100, round(score, 2)))