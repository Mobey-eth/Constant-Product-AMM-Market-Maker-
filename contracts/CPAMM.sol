// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "./IERC20.sol";

contract CPAMM {
    IERC20 public immutable token0;
    IERC20 public immutable token1;

    uint256 public TotalSupply;
    uint256 public reserve0;
    uint256 public reserve1;

    mapping(address => uint256) public balanceOf;
    mapping(address => bool) public isLp;

    event Mint(address indexed To, uint256 Shares);
    event Burn(address indexed From, uint256 Shares);

    error PriceDiscrepancy();

    event AddLiquidity(
        address indexed LP,
        uint256 amount0In,
        uint256 amount1In
    );

    event Swap(
        address indexed User,
        address TokenIn,
        uint256 amountIn,
        uint256 amountOut
    );

    event RemoveLiquidity(
        address indexed LP,
        uint256 amount0Out,
        uint256 amount1Out
    );

    constructor(address _token0, address _token1) {
        token0 = IERC20(_token0);
        token1 = IERC20(_token1);
    }

    function mint(address _to, uint256 _shares) private {
        balanceOf[_to] += _shares;
        TotalSupply += _shares;
        emit Mint(_to, _shares);
    }

    function burn(address _from, uint256 _shares) private {
        balanceOf[_from] -= _shares;
        TotalSupply -= _shares;
        emit Burn(_from, _shares);
    }

    function updateReserves(uint256 _res0, uint256 _res1) private {
        reserve0 = _res0;
        reserve1 = _res1;
    }

    function addLiquidity(uint256 _amount0, uint256 _amount1)
        public
        returns (uint256 shares)
    {
        require(_amount0 > 0 && _amount1 > 0, "amount must be greater than 0!");

        // check for dy/dx == Y/X => (Xdy == Ydx)
        if (reserve0 * _amount1 != reserve1 * _amount0) {
            revert PriceDiscrepancy();
        }
        // require(_amount0 == _amount1, "Unequal amounts of tokens!");
        token0.transferFrom(msg.sender, address(this), _amount0);
        token1.transferFrom(msg.sender, address(this), _amount1);

        // I didn't call these fxn's to save gas, prolly should...
        // uint256 bal0 = token0.balanceOf(address(this));
        // uint256 bal1 = token1.balanceOf(address(this));

        /*
            To mint shares;
            f(x,y) = value of liq = sqrt(xy)
            s = dx / x * T = dy / y * T
        */

        if (TotalSupply == 0) {
            shares = _sqrt(_amount0 * _amount1);
        } else {
            shares = _min(
                (_amount0 * TotalSupply) / reserve0,
                (_amount1 * TotalSupply) / reserve1
            );
        }
        require(shares > 0, "shares = 0!");
        mint(msg.sender, shares);
        // update reserves
        updateReserves(
            token0.balanceOf(address(this)),
            token1.balanceOf(address(this))
        );
        isLp[msg.sender] = true;
        emit AddLiquidity(msg.sender, _amount0, _amount1);
    }

    function swap(address _tokenIn, uint256 _amountIn)
        external
        returns (uint256 amountOut)
    {
        require(_amountIn > 0, "amount must be greater than 0!");
        require(
            _tokenIn == address(token0) || _tokenIn == address(token1),
            "Unsupported token"
        );

        bool isToken0 = _tokenIn == address(token0);

        (
            IERC20 tokenIn,
            IERC20 tokenOut,
            uint256 resIn,
            uint256 resOut
        ) = isToken0
                ? (token0, token1, reserve0, reserve1)
                : (token1, token0, reserve1, reserve0);

        tokenIn.transferFrom(msg.sender, address(this), _amountIn);

        // to extract the fees of 0.3%
        uint256 amountIn = (_amountIn * 997) / 1000;

        amountOut = (resOut * amountIn) / (resIn + amountIn);
        tokenOut.transfer(msg.sender, amountOut);

        updateReserves(
            token0.balanceOf(address(this)),
            token1.balanceOf(address(this))
        );

        emit Swap(msg.sender, _tokenIn, _amountIn, amountOut);
    }

    function removeLiquidity(uint256 _shares)
        public
        returns (uint256 amount0Out, uint256 amount1Out)
    {
        require(_shares > 0, "Shares must be greater that zero!");
        require(isLp[msg.sender], "msg.sender != Liquidity provider!");
        require(
            balanceOf[msg.sender] > 0,
            "You don't have any remaining shares"
        );

        // to calculate the amount of tokens to burn from the eqn
        // (X *s)/T || (Y *s)/T

        uint256 bal0 = token0.balanceOf(address(this));
        uint256 bal1 = token1.balanceOf(address(this));

        amount0Out = (bal0 * _shares) / TotalSupply;
        amount1Out = (bal1 * _shares) / TotalSupply;

        require(
            amount0Out > 0 && amount1Out > 0,
            "Cannot transfer zero tokens!"
        );

        burn(msg.sender, _shares);

        updateReserves(bal0 - amount0Out, bal1 - amount1Out);

        token0.transfer(msg.sender, amount0Out);
        token1.transfer(msg.sender, amount1Out);

        if (balanceOf[msg.sender] == 0) {
            isLp[msg.sender] = false;
        }
        // to make this function reentrancy proof.
        emit RemoveLiquidity(msg.sender, amount0Out, amount1Out);
    }

    function getReserves()
        external
        view
        returns (
            uint112 reserve0Value,
            uint112 reserve1Value,
            uint32 blockTimestampLast
        )
    {
        blockTimestampLast = uint32(block.timestamp);
        reserve0Value = uint112(reserve0);
        reserve1Value = uint112(reserve1);
    }

    function _sqrt(uint256 y) private pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }

    function _min(uint256 _x, uint256 _y) private pure returns (uint256) {
        return _x <= _y ? _x : _y;
    }
}
