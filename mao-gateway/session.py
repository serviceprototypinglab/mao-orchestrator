from sqlalchemy import create_engine
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import configparser


config = configparser.ConfigParser()
config.read('session.ini')
postgres_user = config['POSTGRES']['USER']
postgres_pass = config['POSTGRES']['PASSWORD']
postgres_db = config['POSTGRES']['DB']
postgres_host = config['POSTGRES']['HOST']

db_string = 'postgresql://{}:{}@{}/{}'.format(postgres_user, postgres_pass,
                                              postgres_host, postgres_db)

db = create_engine(db_string)
base = declarative_base()


class Node(base):
    __tablename__ = 'nodes'
    username = Column(String, primary_key=True)
    ip = Column(String)
    location = Column(String)


Session = sessionmaker(db)
session = Session()

base.metadata.create_all(db)


def create(username, ip, location):
    testnode = Node(username=username, ip=ip, location=location)
    session.add(testnode)
    session.commit()


def get_ips():
    ips = []
    nodes = session.query(Node)
    for node in nodes:
        ips.append(node.ip)
    return ips

# Update
#testnode.username = "Some2016Film"
#session.commit()

# Delete
#session.delete(testnode)
#session.commit()
