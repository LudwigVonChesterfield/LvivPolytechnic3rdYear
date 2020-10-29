c = 1
m = 2**11 - 1
a = 3**5
x = 4

primes = []


def gen_primes(x):
    if x <= len(primes):
        return primes

    i = max(len(primes), 2)
    while i <= x:
        prime = True
        for prime in primes:
            if i % prime == 0:
                prime = False
                break
        if prime:
            primes.append(i)
        i += 1

    return primes


def gen_primes_up_to(a):
    primes = gen_primes(a)
    retVal = []
    for prime in primes:
        if prime > a:
            break
        retVal.append(prime)
    return retVal


def gen_rand(x):
    return (x * a + c) % m


def factorize(a):
    factors = set()

    smallprimes = []

    limit = int(a ** 0.5) + 1
    pos_primes = gen_primes_up_to(limit)

    for prime in pos_primes:
        if a % prime == 0:
            smallprimes.append(prime)

    factors.update(smallprimes)
    for prime in smallprimes:
        factors.update(factorize(a / prime))
    return factors


def are_coprime(a, b):
    factors_a = factorize(a)
    factors_b = factorize(b)

    return factors_a.isdisjoint(factors_b)


def output(f, x):
    print(x)
    f.write(str(x) + "\n")


print("Analysing coefficients:")
c_m_coprime = are_coprime(c, m)
b = a - 1
m_factors = factorize(m)
b_is_multiple_of_m_factors = True
for factor in m_factors:
    if b % factor != 0:
        b_is_multiple_of_m_factors = False
        break
b_4_m_4 = True
if m % 4 == 0 and b % 4 != 0:
    b_4_m_4 = False

if c_m_coprime and b_is_multiple_of_m_factors and b_4_m_4:
    print("The period is full.")
else:
    print("The period can not be full.")


period = 0
with open("file.txt", 'w') as f:
    x1 = gen_rand(x)

    n = int(input("Please enter a number of random numbers to generate."))

    i = 0
    while period == 0 or i < n:
    # for i in range(n):
        i += 1
        x = gen_rand(x)
        if i < n:
            output(f, x)

        if i != 1 and x == x1 and period == 0:
            period = i

    if period != 0 and n < m:
        print(
            "Period is less than m(and equals to " +
            str(period) +
            "), thus it is not full.")
