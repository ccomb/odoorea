# coding: utf-8


def Zero():
    def contract(now, provider, receiver):
        return []
    return contract


def One(rt):
    def contract(now, provider, receiver):
        # TODO move to the contract, return 1 instead
        return [{
            'resource_type': rt,
            'quantity': 1,
            'acquisition_date': now,
            'horizon': 0,
            'provider': provider,
            'receiver': receiver}]
    return contract


def Give(cs):
    def contract(now, provider, receiver):
        return [c(now, receiver, provider) for c in cs]
    return contract


def And(cs1, cs2):
    def contract(now, provider, receiver):
        return (cs1(now, provider, receiver)
                + cs2(now, provider, receiver))
    return contract


def Scale(obs, cs):
    def contract(now, provider, receiver):
        result = []
        for c in cs(now, provider, receiver):
            c['quantity'] *= obs
            result.append(c)
        return result
    return contract


def When(obs, cs):
    def contract(now, provider, receiver):
        result = []
        for c in cs(now, provider, receiver):
            if not obs:
                continue
            result.append(c)
        return result
    return contract


def Or(cs1, cs2):
    def contract(now, provider, receiver):
        # ajouter un choix dans le paramètre d'évaluation du contrat ?
        # renvoyer une fonction qui affiche la prochaine date de choix
        # ou qui propose le choix, ou qui prend le choix en argument ?
        if input("1 or 2 ? ") == '1':
            return cs1(now, provider, receiver)
        else:
            return cs2(now, provider, receiver)
    return contract


def Cond(obs, cs1, cs2):
    def contract(now, provider, receiver):
        if obs:
            return cs1(now, provider, receiver)
        else:
            return cs2(now, provider, receiver)


def Truncate(obs, cs):
    def contract(now, provider, receiver):
        result = []
        for c in cs(now, provider, receiver):
            c['horizon'] = min(obs, c['horizon'])
            result.append(c)
        return result
    return contract


def Then(cs1, cs2):
    def contract(now, provider, receiver):
        for cs in (cs1, cs2):
            result = []
            for c in cs(now, provider, receiver):
                if now < c['horizon']:
                    result.append(c)
            if result:
                return result
        return []
    return contract


def Get(cs):
    def contract(now, provider, receiver):
        result = []
        for c in cs(now, provider, receiver):
            if now < c['horizon']:
                return []
            else:
                result.append(c)
        return result
    return contract


def Anytime(cs):
    def contract(now, provider, receiver):
        result = []
        for c in cs(now, provider, receiver):
            if input('trigger? (y/n): ') == 'y':
                result.append(c)
        return result
    return contract


def Until(obs, cs):
    def contract(now, provider, receiver):
        if obs:
            return []
        else:
            return cs(now, provider, receiver)


def Konst(i):
    def obs():
        return i
    return obs
