import pytest

@pytest.mark.django_db
def test_ChatStatus_create():
    from eeclass_line_bot.models import ChatStatus
    status = ChatStatus.objects.get_or_create(line_user_id="test_id", status='test_status', propagation=True)[0]
    assert status.line_user_id=='test_id'
    assert status.status=='test_status'
    assert status.propagation==True
