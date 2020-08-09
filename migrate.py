from web import db

db.reflect()
db.drop_all()
db.create_all()
db.session.commit()
