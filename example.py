from awscalc import *

resources = [
    EC2('web asg', size='m5.large', count=2),
    EC2('nfs', size='c5.large'),
    NLB('web nlb', connections=300, duration=120, bandwidth=1000),
    ALB('web alb', connections=300, duration=120, bandwidth=1000, requests=50, rules=60)
]

calc = Calculator('us-west-2')

for res in resources:
    calc.add(res)

print(calc.resources)
print(calc.total)
