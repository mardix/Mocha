
from juice import Juice
from harambe.decorators import extends
from harambe.packages import contact_page
from tests import config

def test_contact_page():

    @extends(contact_page.contact_page)
    class Index(Juice):
        pass

    app = Juice.init(__name__, config=config)
    app.testing = True

    with app.test_client() as c:
        data = c.get("/contact").data
