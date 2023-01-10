import click
from cli.calculator import main as cal_main

@click.group()
def main():
    pass

@main.command()
@click.option('-v1', '--var1', default=2)
@click.option('-v2', '--var2', default=1)
def add(var1, var2):
    """덧셈함수
    """
    from batch.celery.tasks.calculator import add
    print(add(
        x=var1, y=var2
    ))

@main.command()
@click.option('-v1', '--var1', default=2)
@click.option('-v2', '--var2', default=1)
def mul(var1, var2):
    """곱셈함수
    """
    from batch.celery.tasks.calculator import mul
    print(mul(
        x=var1, y=var2
    ))


main.add_command(cal_main, 'cal-main' )

if __name__ == '__main__':
    main()