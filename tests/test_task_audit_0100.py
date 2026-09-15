import json
from uuid import uuid4

from familienportal.models import User
from familienportal.task_audit import audit_task
from familienportal.task_models import FamilyTask


class FakeDB:
    def __init__(self): self.items=[]
    def add(self,item): self.items.append(item)


def test_audit_does_not_store_task_title_or_description():
    family_id=uuid4(); user=User(id=uuid4(),family_id=family_id,email="a@example.test",display_name="A",password_hash="x")
    task=FamilyTask(id=uuid4(),family_id=family_id,creator_user_id=user.id,title="Geheime Aufgabe",description="Privater Inhalt",is_private=True)
    db=FakeDB(); event=audit_task(db,"task.created",user,task)
    assert "Geheime Aufgabe" not in event.details
    assert "Privater Inhalt" not in event.details
    assert json.loads(event.details)["is_private"] is True


def test_audit_targets_task_and_actor_family():
    family_id=uuid4(); user=User(id=uuid4(),family_id=family_id,email="a@example.test",display_name="A",password_hash="x")
    task=FamilyTask(id=uuid4(),family_id=family_id,creator_user_id=user.id,title="Test")
    event=audit_task(FakeDB(),"task.completed",user,task,previous_status="open")
    assert event.family_id==family_id
    assert event.actor_user_id==user.id
    assert event.target_type=="family_task"
    assert event.target_id==str(task.id)
    assert json.loads(event.details)["previous_status"]=="open"
