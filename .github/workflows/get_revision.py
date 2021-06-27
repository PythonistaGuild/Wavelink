import requests


def getrev() -> str:
    resp = requests.get("https://pypi.org/pypi/wavelink/json")
    data = sorted(resp.json()["releases"])

    first = max(data).split('b')[0]
    second = sorted([int(p.split('b')[1]) for p in data if 'b' in p], reverse=True)[0]

    final = f"{first}b{int(second) + 1}"

    return final


print(getrev())
