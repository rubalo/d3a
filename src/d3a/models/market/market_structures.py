from collections import namedtuple


class Offer:
    def __init__(self, id, price, energy, seller):
        self.id = str(id)
        self.real_id = id
        self.price = price
        self.energy = energy
        self.seller = seller

    def __repr__(self):
        return "<Offer('{s.id!s:.6s}', '{s.energy} kWh@{s.price}', '{s.seller} {rate}'>"\
            .format(s=self, rate=self.price / self.energy)

    def __str__(self):
        return "{{{s.id!s:.6s}}} [{s.seller}]: {s.energy} kWh @ {s.price} @ {rate}"\
            .format(s=self, rate=self.price / self.energy)


class Bid(namedtuple('Bid', ('id', 'price', 'energy', 'buyer', 'seller', 'market'))):
    def __new__(cls, id, price, energy, buyer, seller, market=None):
        # overridden to give the residual field a default value
        return super(Bid, cls).__new__(cls, str(id), price, energy, buyer, seller, market)

    def __repr__(self):
        return (
            "<Bid {{{s.id!s:.6s}}} [{s.buyer}] [{s.seller}] "
            "{s.energy} kWh @ {s.price} {rate}>".format(s=self, rate=self.price / self.energy)
        )

    def __str__(self):
        return (
            "{{{s.id!s:.6s}}} [{s.buyer}] [{s.seller}] "
            "{s.energy} kWh @ {s.price} {rate}".format(s=self, rate=self.price / self.energy)
        )


class Trade(namedtuple('Trade', ('id', 'time', 'offer', 'seller',
                                 'buyer', 'residual', 'price_drop',
                                 'already_tracked'))):
    def __new__(cls, id, time, offer, seller, buyer, residual=None,
                price_drop=False, already_tracked=False):
        # overridden to give the residual field a default value
        return super(Trade, cls).__new__(cls, id, time, offer, seller, buyer, residual,
                                         price_drop, already_tracked)

    def __str__(self):
        mark_partial = "(partial)" if self.residual is not None else ""
        return (
            "{{{s.id!s:.6s}}} [{s.seller} -> {s.buyer}] "
            "{s.offer.energy} kWh {p} @ {s.offer.price} {rate} {s.offer.id}".
            format(s=self, p=mark_partial, rate=self.offer.price / self.offer.energy)
        )

    @classmethod
    def _csv_fields(cls):
        return (cls._fields[:2] + ('rate [ct./kWh]', 'energy [kWh]') +
                cls._fields[3:5])

    def _to_csv(self):
        rate = round(self.offer.price / self.offer.energy, 4)
        return self[:2] + (rate, self.offer.energy) + self[3:5]


class BalancingOffer(Offer):

    def __repr__(self):
        return "<BalancingOffer('{s.id!s:.6s}', '{s.energy} kWh@{s.price}', '{s.seller} {rate}'>"\
            .format(s=self, rate=self.price / self.energy)

    def __str__(self):
        return "<BalancingOffer{{{s.id!s:.6s}}} [{s.seller}]: " \
               "{s.energy} kWh @ {s.price} @ {rate}>".format(s=self,
                                                             rate=self.price / self.energy)


class BalancingTrade(namedtuple('BalancingTrade', ('id', 'time', 'offer', 'seller',
                                                   'buyer', 'residual', 'price_drop'))):
    def __new__(cls, id, time, offer, seller, buyer, residual=None, price_drop=False):
        # overridden to give the residual field a default value
        return super(BalancingTrade, cls).__new__(cls, id, time, offer, seller,
                                                  buyer, residual, price_drop)

    def __str__(self):
        mark_partial = "(partial)" if self.residual is not None else ""
        return (
            "{{{s.id!s:.6s}}} [{s.seller} -> {s.buyer}] "
            "{s.offer.energy} kWh {p} @ {s.offer.price} {rate} {s.offer.id}".
            format(s=self, p=mark_partial, rate=self.offer.price / self.offer.energy)
        )

    @classmethod
    def _csv_fields(cls):
        return (cls._fields[:2] + ('rate [ct./kWh]', 'energy [kWh]') +
                cls._fields[3:5])

    def _to_csv(self):
        rate = round(self.offer.price / self.offer.energy, 4)
        return self[:2] + (rate, self.offer.energy) + self[3:5]
