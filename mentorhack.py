from flask import Flask, request
from pymongo import MongoClient
from bson.objectid import ObjectId
import vk
import re
import json
from collections import Counter
import web

app = Flask(__name__)

db = MongoClient().mentorhack

session = vk.Session(access_token='7aa240bd62486472f05c8457cc24b63fec822359d30cbb79dcce625b76b09b16e7faa83ce547ee0f34d1e')

api = vk.API(session)

'''
Верификация: контроль за компетенциями от независимых наблюдателей GRAPHENE!!!!!

Сосредоточиться на алгоритмах поиска и сравнения.
'''

def update_personal(id,input):
    db.person.update_one({'_id': ObjectId(id)}, {'$set': input})


def get_vk(user_id):
    link = db.person.find_one({'_id': ObjectId(user_id)})['vk'].split('/')[-1]
    vk_info = api.users.get(user_ids=link,
                            fields=['status', 'activities', 'interests', 'music', 'movies', 'tv', 'books', 'games',
                                    'about', 'quotes', 'personal'])[0]
    del vk_info['first_name']
    del vk_info['last_name']
    groups = []
    api.wall.get(domain=link)
    for i in api.groups.getById(group_ids=api.groups.get(user_id=vk_info['uid']),
                                fields=['description', 'activity', 'status']):
        try:
            description = i['description']
        except:
            description = ''
        try:
            status = i['status']
        except:
            status = ''
        groups.append({'name': i['name'], 'description': re.sub('<br>', ' ', description), 'status': status})
    vk_info['groups'] = groups
    text = ''
    for i in vk_info['wall']:
        text += i
    for i in vk_info['groups']:
        text += i['description']
    tag_arr = re.findall(r'(\w+)', re.sub('.', ' ',re.sub(',', ' ', re.sub('<br>', ' ', text))))

    cnt = Counter()
    for word in tag_arr:
        if len(word) > 2:
            cnt[word] += 1
            popular = cnt.most_common(100)

    ex = ['com', 'для', 'что', 'это', 'https', 'http', 'как', 'или', 'группы', 'группа', 'нас', 'уже', 'все', 'всех',
          'так', 'если', "здесь", "только"]

    top = []
    for i in popular:
        top.append(i[0])

    tags = [x for x in top if x not in ex]

    db.vk_info.insert_one({'user_id':user_id, 'vk_info':vk_info, 'tags': tags})


def compare_personal(id1,id2):
    user1 = db.person.find_one({'user_id':ObjectId(id1)})
    user2 = db.person.find_one({'user_id':ObjectId(id2)})
    temp1 = []
    temp2 = []
    for i in user1['groups']:
        temp1.append(i['name'])
    for i in user2['groups']:
        temp2.append(i['name'])
    com_groups = list(set(temp1) & set(temp2))


def get_tags(user_id):
    pass



@app.route('/')
def index():
    return 'Hola'


@app.route('/api/users/create', methods=['POST'])
def create_user():
    input = request.get_json(force=True)
    print(input)
    id = json.dumps({'token': str(db.users.insert(input))})

    return id

if __name__ == '__main__':
    app.run()
