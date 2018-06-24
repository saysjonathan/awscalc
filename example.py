from awscalc import *

resources = [
    EC2("web asg", size="m5.large", count=2),
    EC2("nfs", size="c5.large"),
    ALB(
        "web alb", connections=300, duration=120, bandwidth=1000, requests=50, rules=60
    ),
    EBS("web ebs", count=2, size=100),
    EBS("nfs ebs", size=1000),
    RDS("rds", count=2, size="db.r4.large", engine="Aurora MySQL"),
    EBS("rds ebs", count=2, size=100),
]

calc = Calculator("us-west-2")

for res in resources:
    calc.add(res)

print(calc.resources)
print("{:.2f}".format(calc.total))
