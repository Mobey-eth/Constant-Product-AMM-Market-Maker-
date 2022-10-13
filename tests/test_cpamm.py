from brownie import CPAMM, MobiCoin, NinaCoin, interface, accounts, web3
import pytest


def test_deploy_tokens():
    zero_address = "0x0000000000000000000000000000000000000000"
    deployer = accounts[0]
    user = accounts[1]
    user1 = accounts[2]
    user2 = accounts[3]
    user3 = accounts[4]
    Lp2 = accounts[5]

    get_thousand = web3.toWei(1000, "ether")
    get_hundred = web3.toWei(100, "ether")
    get_fifty = web3.toWei(50, "ether")
    mobi_coin = MobiCoin.deploy(get_thousand, {"from": deployer})
    nina_coin = NinaCoin.deploy(get_thousand, {"from": deployer})

    mobi_coin_interface = interface.IERC20(mobi_coin.address)
    nina_coin_interface = interface.IERC20(nina_coin.address)

    mobi_coin_interface.mintMore(get_thousand, {"from": user})
    nina_coin_interface.mintMore(get_thousand, {"from": user})

    mobi_coin_interface.mintMore(get_hundred, {"from": user1})
    nina_coin_interface.mintMore(get_hundred, {"from": user1})

    mobi_coin_interface.mintMore(get_hundred, {"from": user2})
    nina_coin_interface.mintMore(get_hundred, {"from": user2})

    mobi_coin_interface.mintMore(get_fifty, {"from": user3})
    nina_coin_interface.mintMore(get_fifty, {"from": user3})

    mobi_coin_interface.mintMore(get_fifty, {"from": Lp2})
    nina_coin_interface.mintMore(get_fifty, {"from": Lp2})

    print(
        f"Deployer Token balance is: {web3.fromWei(mobi_coin.balanceOf(deployer.address), 'ether')} {mobi_coin.symbol()}, {web3.fromWei(nina_coin.balanceOf(deployer.address), 'ether')} {nina_coin.symbol()} "
    )

    print(
        "User Token balance is: ",
        web3.fromWei(mobi_coin_interface.balanceOf(user.address), "ether"),
        mobi_coin_interface.symbol(),
        ",",
        web3.fromWei(nina_coin_interface.balanceOf(user.address), "ether"),
        nina_coin_interface.symbol(),
    )

    return (
        deployer,
        user,
        mobi_coin,
        nina_coin,
        get_thousand,
        get_hundred,
        get_fifty,
        zero_address,
        user1,
        user2,
        user3,
        Lp2,
    )


def test_cpamm_contract():
    (
        deployer,
        user,
        mobi_coin,
        nina_coin,
        get_thousand,
        get_hundred,
        get_fifty,
        zero_address,
        user1,
        user2,
        user3,
        Lp2,
    ) = test_deploy_tokens()

    cpamm_contract = CPAMM.deploy(
        mobi_coin.address, nina_coin.address, {"from": deployer}
    )
    assert cpamm_contract.reserve0() == 0
    assert cpamm_contract.reserve1() == 0
    assert cpamm_contract.TotalSupply() == 0

    print("State variables are okay!")
    print("Adding Liquidity!!")
    tx1 = mobi_coin.approve(cpamm_contract.address, get_thousand, {"from": deployer})
    tx2 = nina_coin.approve(cpamm_contract.address, get_thousand, {"from": deployer})

    tx1a = mobi_coin.approve(cpamm_contract.address, get_hundred, {"from": user})
    tx2a = nina_coin.approve(cpamm_contract.address, get_hundred, {"from": user})

    mobi_coin.approve(cpamm_contract.address, get_hundred, {"from": user1})
    nina_coin.approve(cpamm_contract.address, get_hundred, {"from": user1})

    mobi_coin.approve(cpamm_contract.address, get_hundred, {"from": user2})
    nina_coin.approve(cpamm_contract.address, get_hundred, {"from": user2})

    mobi_coin.approve(cpamm_contract.address, get_fifty, {"from": user3})
    nina_coin.approve(cpamm_contract.address, get_fifty, {"from": user3})

    mobi_coin.approve(cpamm_contract.address, get_fifty, {"from": Lp2})
    nina_coin.approve(cpamm_contract.address, get_fifty, {"from": Lp2})
    # tx1.info()

    # tx2.info()
    print("Approve success for deployer!")
    tx3 = cpamm_contract.addLiquidity(get_thousand, get_thousand, {"from": deployer})
    lp2tx = cpamm_contract.addLiquidity(get_fifty, get_fifty, {"from": Lp2})
    print("Logging add liquidity events...")
    print(tx3.events["AddLiquidity"])
    print(lp2tx.events["AddLiquidity"])
    print(tx3.events["Mint"])

    print("logging reserves")
    print(f"The pool reserve balances are : {cpamm_contract.getReserves()}")
    print(f"The total supply of shares = {cpamm_contract.TotalSupply()}")
    shares_deployer = cpamm_contract.balanceOf(deployer.address)
    shares_lp2 = cpamm_contract.balanceOf(Lp2.address)
    print(f"The deployer/ LP1 total shares is = {shares_deployer} ")
    print(f"The LP2 total shares is = {shares_lp2} ")

    # tx3.info()
    # print(web3.fromWei(cpamm_contract.balanceOf(deployer.address), "ether"))

    tx4 = cpamm_contract.swap(mobi_coin.address, get_hundred, {"from": user})
    cpamm_contract.swap(mobi_coin.address, get_hundred, {"from": user1})
    cpamm_contract.swap(nina_coin.address, get_hundred, {"from": user2})
    txninacoin = cpamm_contract.swap(nina_coin.address, get_fifty, {"from": user3})
    print("tx's complete!")
    tx4.info()
    txninacoin.info()

    print("logging reserves")
    print(f"The pool reserve balances are : {cpamm_contract.getReserves()}")

    print("----------------------------------getting shares ---------------------")
    print(
        f"The deployer/ LP1 total shares is = {cpamm_contract.balanceOf(deployer.address)} "
    )
    print(f"The LP2 total shares is = {cpamm_contract.balanceOf(Lp2.address)} ")

    tx5 = cpamm_contract.removeLiquidity(shares_deployer, {"from": deployer})
    print(tx5.events["Burn"])
    print(tx5.events["RemoveLiquidity"])
    print("logging reserves")
    print(f"The pool reserve balances are : {cpamm_contract.getReserves()}")

    tx6 = cpamm_contract.removeLiquidity(shares_lp2, {"from": Lp2})
    print(tx6.events["RemoveLiquidity"])
    print("logging reserves")
    print(f"The pool reserve balances are : {cpamm_contract.getReserves()}")


# function is internal ... Don't run without changing visibility
@pytest.mark.parametrize("num", [9, 1, 16, 36, 100, 144])
def test_sqrt(num):
    account = accounts[0]
    get_thousand = web3.toWei(1000, "ether")
    get_hundred = web3.toWei(100, "ether")
    get_fifty = web3.toWei(50, "ether")
    mobi_coin = MobiCoin.deploy(get_thousand, {"from": account})
    nina_coin = NinaCoin.deploy(get_thousand, {"from": account})

    cpamm_contract = CPAMM.deploy(
        mobi_coin.address, nina_coin.address, {"from": account}
    )

    sqrt = cpamm_contract._sqrt(num)
    print(f"The value of square root is {sqrt}")

    chek = cpamm_contract._min(19, 20)
    print(chek)
