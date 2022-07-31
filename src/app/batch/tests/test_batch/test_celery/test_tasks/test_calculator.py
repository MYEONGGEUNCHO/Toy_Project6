from batch.celery.tasks.calculator import add, mul
def test_add():
    print(add(2, 1))

def test_mul():
    print(mul(2, 1))