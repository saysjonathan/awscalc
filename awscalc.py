import json
import boto3


regions = {
    "us-east-1": "US East (N. Virigina)",
    "us-east-2": "US East (Ohio)",
    "us-west-1": "US West (California)",
    "us-west-2": "US West (Oregon)",
}


class Field:
    def __init__(self, attr, default, req):
        self.attr = attr
        self.default = default
        self.req = req
        self._value = None

    @property
    def value(self):
        return self._value or self.default

    @value.setter
    def value(self, val):
        self._value = val

    def to_filter(self):
        if self.attr is not None:
            return {
                "Type": "TERM_MATCH",
                "Field": self.attr,
                "Value": self.value or self.default,
            }


class Resource:
    def __init__(self, tag, **kwargs):
        self.tag = tag
        for name, field in self._fields.items():
            setattr(self, name, Field(*field))

        for k, v in kwargs.items():
            field = getattr(self, k)
            if field:
                field.value = v
            else:
                raise ValueError("unknown field: {}".format(k))

    def filters(self, region):
        if self.region.value == None:
            self.region.value = region

        self.region.value = regions[self.region.value]

        filters = []
        for field in self._fields.keys():
            f = getattr(self, field)
            filter = f.to_filter()
            if filter != None:
                filters.append(filter)

        return filters

    def _pricelist(self, client, region):
        response = client.get_products(
            ServiceCode=self.code.value, Filters=self.filters(region)
        )
        return response["PriceList"]

    def _terms(self, term):
        return next(iter(next(iter(next(iter(term.values())).values())).values()))

    def _ppu(self, price):
        return float(price["pricePerUnit"]["USD"])


class EC2(Resource):
    _fields = {
        "code": ("serviceCode", "AmazonEC2", False),
        "count": (None, 1, False),
        "family": ("productFamily", "Compute Instance", False),
        "os": ("operatingSystem", "Linux", False),
        "region": ("location", None, False),
        "size": ("instanceType", None, True),
        "sw": ("preInstalledSw", "NA", False),
        "tenancy": ("tenancy", "Shared", False),
        "term": (None, "OnDemand", False),
    }

    def price(self, client, region, hours):
        pricelist = self._pricelist(client, region)
        term = json.loads(pricelist[0])["terms"][self.term.value]
        price = self._terms(term)
        return self._ppu(price) * hours * self.count.value


class NLB(Resource):
    _fields = {
        "bandwidth": (None, None, True),
        "code": ("serviceCode", "AmazonEC2", False),
        "connections": (None, None, True),
        "duration": (None, None, True),
        "count": (None, None, True),
        "family": ("productFamily", "Load Balancer-Network", False),
        "region": ("location", None, False),
        "term": (None, "OnDemand", False),
    }

    def price(self, client, region, hours):
        pricelist = self._pricelist(client, region)

        hrs = 0.00
        lcu = 0.00

        for term in pricelist:
            t = json.loads(term)["terms"][self.term.value]
            price = self._terms(t)
            if price["unit"] == "Hrs":
                hrs = self._ppu(price)
            else:
                lcu = self._ppu(price)

        new = 800
        active = 100000
        bandwidth = 1

        new_lcu = self.connections.value / new
        active_lcu = (self.connections.value * self.duration.value) / 100000
        bw_lcu = (self.bandwidth.value / hours) / bandwidth
        max_lcu = max(new_lcu, active_lcu, bw_lcu)

        return (hrs * hours) + (lcu * max_lcu * hours)


class Calculator:
    def __init__(self, region, hours=732):
        self.resources = {}
        self.total = 0.00
        self._region = region
        self._hours = hours
        self._client = boto3.client("pricing", region_name="us-east-1")

    def add(self, resource):
        if resource.tag in self.resources:
            raise ValueError("Duplicate resource: {}".format(tag))
        price = resource.price(self._client, self._region, self._hours)
        self.resources[resource.tag] = price
        self.total += price
