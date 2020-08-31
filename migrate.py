from web import db
from web.models import VKUser, STATUS_ADMIN


db.reflect()
db.drop_all()
db.create_all()
db.session.commit()

superuser = VKUser(98626188, status=STATUS_ADMIN)
superuser.update_pd()
superuser.save()
