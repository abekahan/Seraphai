"""
Crypto Mortgage Prospecting Service

A permissionless prospecting tool that identifies and scores mortgage-qualified
crypto holders without any wallet connection required. Uses public blockchain
data to analyze wallets and score them for mortgage qualification.

Core Concept: Reverse Funnel
Instead of waiting for customers, proactively identify qualified crypto holders.
"""

import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import json


class RiskTier(Enum):
    """Risk classification for crypto holders"""
    PRIME = "prime"           # Highest quality prospects
    NEAR_PRIME = "near_prime" # Good prospects with minor flags
    SUBPRIME = "subprime"     # Higher risk prospects
    UNQUALIFIED = "unqualified"


class WalletBehavior(Enum):
    """Behavioral classification based on on-chain activity"""
    HODLER = "hodler"           # Long-term holder, minimal trading
    ACCUMULATOR = "accumulator" # Regularly adding to positions
    ACTIVE_TRADER = "active_trader"  # Frequent trading activity
    DEFI_POWER_USER = "defi_power_user"  # Heavy DeFi participation
    YIELD_FARMER = "yield_farmer"  # Staking/farming focus
    WHALE = "whale"             # Very large holdings
    DORMANT = "dormant"         # Inactive wallet


@dataclass
class WalletMetrics:
    """Comprehensive metrics for a crypto wallet"""
    address: str
    total_value_usd: float
    eth_balance: float
    token_count: int
    nft_count: int
    first_transaction_date: Optional[str]
    last_transaction_date: Optional[str]
    transaction_count: int
    wallet_age_days: int
    avg_hold_time_days: float
    largest_single_holding_pct: float
    defi_protocol_count: int
    staking_positions: int
    has_ens: bool
    ens_name: Optional[str]
    behavior_type: str
    diversification_score: float


@dataclass
class MortgageQualificationScore:
    """Mortgage qualification scoring for crypto holder"""
    wallet_address: str
    overall_score: float  # 0-100
    risk_tier: str

    # Component scores (0-100 each)
    wealth_score: float
    stability_score: float
    behavior_score: float
    liquidity_score: float
    verification_score: float

    # Qualification metrics
    estimated_annual_income: float
    estimated_net_worth: float
    max_mortgage_amount: float
    recommended_ltv: float

    # Flags and notes
    positive_signals: List[str]
    risk_flags: List[str]
    recommendations: List[str]

    # Contact/outreach info
    contact_methods: List[Dict[str, str]]
    outreach_priority: str  # high, medium, low


@dataclass
class ProspectLead:
    """A qualified prospect lead"""
    wallet_address: str
    qualification_score: float
    risk_tier: str
    estimated_value: float
    behavior_type: str
    contact_methods: List[Dict[str, str]]
    last_active: str
    priority: str
    notes: List[str]


class CryptoProspectingService:
    """
    Permissionless crypto holder prospecting service.

    Analyzes public blockchain data to identify and score mortgage-qualified
    crypto holders without requiring any wallet connection.
    """

    # Minimum thresholds for mortgage consideration
    MIN_WALLET_VALUE_USD = 50000
    MIN_WALLET_AGE_DAYS = 180
    MIN_TRANSACTION_COUNT = 10

    # Scoring weights
    WEALTH_WEIGHT = 0.30
    STABILITY_WEIGHT = 0.25
    BEHAVIOR_WEIGHT = 0.20
    LIQUIDITY_WEIGHT = 0.15
    VERIFICATION_WEIGHT = 0.10

    # API endpoints (public/free tier compatible)
    ETHERSCAN_API = "https://api.etherscan.io/api"
    COINGECKO_API = "https://api.coingecko.com/api/v3"

    def __init__(self, etherscan_api_key: Optional[str] = None):
        """Initialize the prospecting service."""
        self.etherscan_api_key = etherscan_api_key or "YourApiKeyToken"
        self._price_cache = {}
        self._cache_expiry = {}

    def _get_eth_price(self) -> float:
        """Get current ETH price in USD."""
        cache_key = "eth_price"
        if cache_key in self._price_cache:
            if time.time() < self._cache_expiry.get(cache_key, 0):
                return self._price_cache[cache_key]

        try:
            response = requests.get(
                f"{self.COINGECKO_API}/simple/price",
                params={"ids": "ethereum", "vs_currencies": "usd"},
                timeout=10
            )
            if response.status_code == 200:
                price = response.json().get("ethereum", {}).get("usd", 2500)
                self._price_cache[cache_key] = price
                self._cache_expiry[cache_key] = time.time() + 300  # 5 min cache
                return price
        except Exception:
            pass
        return 2500  # Fallback price

    def _get_wallet_balance(self, address: str) -> Dict[str, Any]:
        """Get wallet ETH balance from Etherscan."""
        try:
            response = requests.get(
                self.ETHERSCAN_API,
                params={
                    "module": "account",
                    "action": "balance",
                    "address": address,
                    "tag": "latest",
                    "apikey": self.etherscan_api_key
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1":
                    balance_wei = int(data.get("result", 0))
                    return {"balance_eth": balance_wei / 1e18, "success": True}
        except Exception as e:
            pass
        return {"balance_eth": 0, "success": False}

    def _get_transaction_history(self, address: str, limit: int = 100) -> List[Dict]:
        """Get transaction history for analysis."""
        try:
            response = requests.get(
                self.ETHERSCAN_API,
                params={
                    "module": "account",
                    "action": "txlist",
                    "address": address,
                    "startblock": 0,
                    "endblock": 99999999,
                    "page": 1,
                    "offset": limit,
                    "sort": "desc",
                    "apikey": self.etherscan_api_key
                },
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1":
                    return data.get("result", [])
        except Exception:
            pass
        return []

    def _get_token_holdings(self, address: str) -> List[Dict]:
        """Get ERC20 token holdings."""
        try:
            response = requests.get(
                self.ETHERSCAN_API,
                params={
                    "module": "account",
                    "action": "tokentx",
                    "address": address,
                    "page": 1,
                    "offset": 100,
                    "sort": "desc",
                    "apikey": self.etherscan_api_key
                },
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1":
                    return data.get("result", [])
        except Exception:
            pass
        return []

    def _classify_behavior(self, transactions: List[Dict], wallet_age_days: int,
                          total_value: float) -> WalletBehavior:
        """Classify wallet behavior based on transaction patterns."""
        if not transactions:
            return WalletBehavior.DORMANT

        tx_count = len(transactions)

        # Calculate transaction frequency
        if wallet_age_days > 0:
            tx_per_month = (tx_count / wallet_age_days) * 30
        else:
            tx_per_month = tx_count

        # Check for DeFi interactions
        defi_protocols = set()
        known_defi = ["uniswap", "aave", "compound", "curve", "maker", "lido", "sushiswap"]
        for tx in transactions:
            to_addr = tx.get("to", "").lower()
            func = tx.get("functionName", "").lower()
            for protocol in known_defi:
                if protocol in to_addr or protocol in func:
                    defi_protocols.add(protocol)

        # Whale check
        if total_value >= 1000000:
            return WalletBehavior.WHALE

        # DeFi power user check
        if len(defi_protocols) >= 3:
            return WalletBehavior.DEFI_POWER_USER

        # Active trader check
        if tx_per_month > 20:
            return WalletBehavior.ACTIVE_TRADER

        # Accumulator check - consistent deposits
        if tx_per_month >= 2 and tx_per_month <= 10:
            return WalletBehavior.ACCUMULATOR

        # Hodler check - low activity, long holding
        if tx_per_month < 2 and wallet_age_days > 365:
            return WalletBehavior.HODLER

        # Yield farmer check
        if "stake" in str(transactions).lower() or "farm" in str(transactions).lower():
            return WalletBehavior.YIELD_FARMER

        return WalletBehavior.ACCUMULATOR  # Default

    def _calculate_diversification(self, eth_balance: float, token_holdings: List[Dict],
                                   eth_price: float) -> float:
        """Calculate portfolio diversification score (0-100)."""
        holdings = {"ETH": eth_balance * eth_price}

        # Aggregate token holdings (simplified)
        for token in token_holdings:
            symbol = token.get("tokenSymbol", "UNKNOWN")
            # Use a simplified value estimation
            if symbol not in holdings:
                holdings[symbol] = 0
            holdings[symbol] += 1  # Count as presence

        total_positions = len(holdings)
        if total_positions == 0:
            return 0

        # More positions = more diversified
        # Score based on number of assets (capped at 20 for max score)
        diversification = min(100, (total_positions / 20) * 100)

        # Penalize if single asset is >50% of holdings
        total_value = sum(holdings.values())
        if total_value > 0:
            max_concentration = max(holdings.values()) / total_value
            if max_concentration > 0.5:
                diversification *= (1 - (max_concentration - 0.5))

        return round(diversification, 2)

    def _resolve_ens(self, address: str) -> Optional[str]:
        """Attempt to resolve ENS name for address."""
        # Simplified - in production would use ENS contract or API
        # For demo, we'll indicate ENS capability
        return None

    def analyze_wallet(self, address: str) -> WalletMetrics:
        """
        Perform comprehensive analysis of a wallet address.

        This is PERMISSIONLESS - no wallet connection needed.
        All data comes from public blockchain records.
        """
        eth_price = self._get_eth_price()

        # Get basic balance
        balance_data = self._get_wallet_balance(address)
        eth_balance = balance_data.get("balance_eth", 0)

        # Get transaction history
        transactions = self._get_transaction_history(address, limit=200)

        # Get token holdings
        token_holdings = self._get_token_holdings(address)

        # Calculate wallet age
        first_tx_date = None
        last_tx_date = None
        wallet_age_days = 0

        if transactions:
            # Transactions are sorted desc, so last item is first tx
            first_tx_timestamp = int(transactions[-1].get("timeStamp", 0))
            last_tx_timestamp = int(transactions[0].get("timeStamp", 0))

            if first_tx_timestamp:
                first_tx_date = datetime.fromtimestamp(first_tx_timestamp).isoformat()
                wallet_age_days = (datetime.now() - datetime.fromtimestamp(first_tx_timestamp)).days

            if last_tx_timestamp:
                last_tx_date = datetime.fromtimestamp(last_tx_timestamp).isoformat()

        # Calculate total value (simplified - ETH + estimated token value)
        total_value = eth_balance * eth_price

        # Count unique tokens
        unique_tokens = set()
        for tx in token_holdings:
            unique_tokens.add(tx.get("tokenSymbol", ""))
        token_count = len(unique_tokens)

        # Estimate token value (simplified - would need price APIs for accuracy)
        # Add rough estimate based on token activity
        estimated_token_value = min(token_count * 1000, total_value * 0.5)
        total_value += estimated_token_value

        # Classify behavior
        behavior = self._classify_behavior(transactions, wallet_age_days, total_value)

        # Calculate diversification
        diversification = self._calculate_diversification(eth_balance, token_holdings, eth_price)

        # Calculate average hold time (simplified)
        avg_hold_time = wallet_age_days * 0.6 if wallet_age_days > 0 else 0

        # Calculate largest holding percentage
        if total_value > 0:
            eth_pct = (eth_balance * eth_price) / total_value * 100
        else:
            eth_pct = 100

        # Count DeFi protocols
        defi_protocols = set()
        known_defi = ["uniswap", "aave", "compound", "curve", "maker", "lido", "yearn"]
        for tx in transactions:
            to_addr = tx.get("to", "").lower()
            for protocol in known_defi:
                if protocol in to_addr:
                    defi_protocols.add(protocol)

        # Check for ENS
        ens_name = self._resolve_ens(address)

        return WalletMetrics(
            address=address,
            total_value_usd=round(total_value, 2),
            eth_balance=round(eth_balance, 4),
            token_count=token_count,
            nft_count=0,  # Would need separate API call
            first_transaction_date=first_tx_date,
            last_transaction_date=last_tx_date,
            transaction_count=len(transactions),
            wallet_age_days=wallet_age_days,
            avg_hold_time_days=round(avg_hold_time, 1),
            largest_single_holding_pct=round(eth_pct, 2),
            defi_protocol_count=len(defi_protocols),
            staking_positions=0,  # Would need protocol-specific checks
            has_ens=ens_name is not None,
            ens_name=ens_name,
            behavior_type=behavior.value,
            diversification_score=diversification
        )

    def _calculate_wealth_score(self, metrics: WalletMetrics) -> float:
        """Calculate wealth score component (0-100)."""
        value = metrics.total_value_usd

        if value < 50000:
            return min(30, value / 50000 * 30)
        elif value < 100000:
            return 30 + ((value - 50000) / 50000) * 20
        elif value < 250000:
            return 50 + ((value - 100000) / 150000) * 20
        elif value < 500000:
            return 70 + ((value - 250000) / 250000) * 15
        elif value < 1000000:
            return 85 + ((value - 500000) / 500000) * 10
        else:
            return min(100, 95 + min(5, (value - 1000000) / 1000000 * 5))

    def _calculate_stability_score(self, metrics: WalletMetrics) -> float:
        """Calculate stability score based on holding patterns (0-100)."""
        score = 0

        # Wallet age component (max 40 points)
        if metrics.wallet_age_days >= 730:  # 2+ years
            score += 40
        elif metrics.wallet_age_days >= 365:  # 1+ year
            score += 30
        elif metrics.wallet_age_days >= 180:  # 6+ months
            score += 20
        else:
            score += (metrics.wallet_age_days / 180) * 20

        # Average hold time component (max 30 points)
        if metrics.avg_hold_time_days >= 365:
            score += 30
        elif metrics.avg_hold_time_days >= 180:
            score += 20
        else:
            score += (metrics.avg_hold_time_days / 180) * 20

        # Diversification component (max 30 points)
        score += metrics.diversification_score * 0.3

        return min(100, score)

    def _calculate_behavior_score(self, metrics: WalletMetrics) -> float:
        """Calculate behavior score based on wallet activity patterns (0-100)."""
        behavior = metrics.behavior_type

        # Base score by behavior type
        behavior_scores = {
            "hodler": 85,
            "accumulator": 90,
            "whale": 80,
            "yield_farmer": 75,
            "defi_power_user": 70,
            "active_trader": 50,
            "dormant": 30
        }

        base_score = behavior_scores.get(behavior, 50)

        # Bonus for DeFi sophistication
        if metrics.defi_protocol_count >= 3:
            base_score += 5

        # Bonus for consistent activity
        if metrics.transaction_count >= 50 and metrics.wallet_age_days >= 365:
            base_score += 5

        return min(100, base_score)

    def _calculate_liquidity_score(self, metrics: WalletMetrics) -> float:
        """Calculate liquidity score (0-100)."""
        score = 0

        # ETH holdings are highly liquid
        eth_value = metrics.eth_balance * self._get_eth_price()
        if eth_value >= 50000:
            score += 50
        else:
            score += (eth_value / 50000) * 50

        # Token diversity suggests ability to liquidate
        if metrics.token_count >= 10:
            score += 30
        else:
            score += (metrics.token_count / 10) * 30

        # Recent activity suggests active management
        if metrics.last_transaction_date:
            try:
                last_tx = datetime.fromisoformat(metrics.last_transaction_date)
                days_since_tx = (datetime.now() - last_tx).days
                if days_since_tx <= 30:
                    score += 20
                elif days_since_tx <= 90:
                    score += 10
            except:
                pass

        return min(100, score)

    def _calculate_verification_score(self, metrics: WalletMetrics) -> float:
        """Calculate verification/identity score (0-100)."""
        score = 50  # Base score for any analyzed wallet

        # ENS name suggests identity commitment
        if metrics.has_ens:
            score += 30

        # Long history provides verification
        if metrics.wallet_age_days >= 365:
            score += 10

        # Transaction count provides verification
        if metrics.transaction_count >= 100:
            score += 10

        return min(100, score)

    def _determine_risk_tier(self, overall_score: float, metrics: WalletMetrics) -> RiskTier:
        """Determine risk tier based on score and metrics."""
        if overall_score >= 75 and metrics.total_value_usd >= 100000:
            return RiskTier.PRIME
        elif overall_score >= 60 and metrics.total_value_usd >= 50000:
            return RiskTier.NEAR_PRIME
        elif overall_score >= 40:
            return RiskTier.SUBPRIME
        else:
            return RiskTier.UNQUALIFIED

    def _generate_signals_and_flags(self, metrics: WalletMetrics, scores: Dict) -> tuple:
        """Generate positive signals and risk flags."""
        positive_signals = []
        risk_flags = []

        # Positive signals
        if metrics.total_value_usd >= 100000:
            positive_signals.append("Substantial crypto holdings (>$100k)")
        if metrics.wallet_age_days >= 730:
            positive_signals.append("Established wallet history (2+ years)")
        if metrics.behavior_type in ["hodler", "accumulator"]:
            positive_signals.append(f"Favorable behavior pattern: {metrics.behavior_type}")
        if metrics.diversification_score >= 70:
            positive_signals.append("Well-diversified portfolio")
        if metrics.defi_protocol_count >= 3:
            positive_signals.append("DeFi-savvy user (multiple protocols)")
        if metrics.has_ens:
            positive_signals.append("ENS domain owner (identity signal)")
        if scores["stability"] >= 70:
            positive_signals.append("High stability score")

        # Risk flags
        if metrics.total_value_usd < 50000:
            risk_flags.append("Holdings below minimum threshold ($50k)")
        if metrics.wallet_age_days < 180:
            risk_flags.append("New wallet (< 6 months)")
        if metrics.behavior_type == "active_trader":
            risk_flags.append("High trading frequency (volatility risk)")
        if metrics.largest_single_holding_pct > 80:
            risk_flags.append("Concentrated position (>80% single asset)")
        if metrics.transaction_count < 10:
            risk_flags.append("Limited transaction history")
        if metrics.behavior_type == "dormant":
            risk_flags.append("Dormant wallet (inactivity concern)")

        return positive_signals, risk_flags

    def _estimate_income(self, metrics: WalletMetrics) -> float:
        """Estimate annual income from on-chain activity."""
        base_income = 0

        # Assumption: crypto holdings correlate with income
        # Conservative multiplier based on typical savings rates
        if metrics.total_value_usd >= 500000:
            base_income = 200000
        elif metrics.total_value_usd >= 250000:
            base_income = 150000
        elif metrics.total_value_usd >= 100000:
            base_income = 100000
        elif metrics.total_value_usd >= 50000:
            base_income = 75000
        else:
            base_income = 50000

        # Adjust for DeFi activity (suggests crypto-native income)
        if metrics.defi_protocol_count >= 3:
            base_income *= 1.2

        # Adjust for accumulator behavior (regular income)
        if metrics.behavior_type == "accumulator":
            base_income *= 1.1

        return round(base_income, 0)

    def _calculate_max_mortgage(self, estimated_income: float, net_worth: float,
                                risk_tier: RiskTier) -> float:
        """Calculate maximum mortgage amount."""
        # Traditional DTI-based calculation
        max_by_income = estimated_income * 5  # 5x income

        # Asset-based lending (crypto as collateral concept)
        max_by_assets = net_worth * 0.5  # 50% of net worth

        # Use the lower of the two for conservative estimate
        base_max = min(max_by_income, max_by_assets)

        # Adjust by risk tier
        tier_multipliers = {
            RiskTier.PRIME: 1.0,
            RiskTier.NEAR_PRIME: 0.85,
            RiskTier.SUBPRIME: 0.7,
            RiskTier.UNQUALIFIED: 0.5
        }

        return round(base_max * tier_multipliers.get(risk_tier, 0.5), 0)

    def _recommend_ltv(self, risk_tier: RiskTier, metrics: WalletMetrics) -> float:
        """Recommend LTV ratio based on risk profile."""
        base_ltv = {
            RiskTier.PRIME: 80,
            RiskTier.NEAR_PRIME: 75,
            RiskTier.SUBPRIME: 70,
            RiskTier.UNQUALIFIED: 60
        }

        ltv = base_ltv.get(risk_tier, 60)

        # Adjust for stability
        if metrics.wallet_age_days >= 730 and metrics.diversification_score >= 70:
            ltv = min(85, ltv + 5)

        return ltv

    def _generate_recommendations(self, metrics: WalletMetrics, risk_tier: RiskTier,
                                  scores: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if risk_tier == RiskTier.PRIME:
            recommendations.append("High-priority prospect - initiate premium outreach")
            recommendations.append("Consider crypto-collateralized mortgage products")
        elif risk_tier == RiskTier.NEAR_PRIME:
            recommendations.append("Good prospect - standard qualification process")
            if scores["stability"] < 70:
                recommendations.append("Request additional holding period documentation")
        elif risk_tier == RiskTier.SUBPRIME:
            recommendations.append("Requires enhanced documentation")
            if metrics.total_value_usd < 50000:
                recommendations.append("May need traditional income verification")
        else:
            recommendations.append("Does not meet current qualification criteria")
            recommendations.append("Consider nurture campaign for future qualification")

        # Specific recommendations
        if metrics.behavior_type == "active_trader":
            recommendations.append("Consider volatility-adjusted qualification")

        if not metrics.has_ens:
            recommendations.append("Request identity verification (no ENS)")

        return recommendations

    def _identify_contact_methods(self, metrics: WalletMetrics) -> List[Dict[str, str]]:
        """Identify possible contact/outreach methods."""
        methods = []

        # ENS-based contact
        if metrics.has_ens and metrics.ens_name:
            methods.append({
                "type": "ens",
                "value": metrics.ens_name,
                "note": "Can message via ENS-linked channels"
            })

        # On-chain messaging
        methods.append({
            "type": "on_chain_message",
            "value": metrics.address,
            "note": "Can send on-chain message transaction"
        })

        # Suggest DeFi community channels based on protocol usage
        if metrics.defi_protocol_count > 0:
            methods.append({
                "type": "defi_community",
                "value": "Protocol Discord/Telegram",
                "note": "Active in DeFi communities - consider targeted ads"
            })

        return methods

    def _determine_outreach_priority(self, overall_score: float,
                                     metrics: WalletMetrics) -> str:
        """Determine outreach priority level."""
        if overall_score >= 80 and metrics.total_value_usd >= 250000:
            return "high"
        elif overall_score >= 60 and metrics.total_value_usd >= 100000:
            return "medium"
        else:
            return "low"

    def score_for_mortgage(self, address: str) -> MortgageQualificationScore:
        """
        Calculate comprehensive mortgage qualification score for a wallet.

        This is the main scoring function that combines all analysis.
        """
        # First, analyze the wallet
        metrics = self.analyze_wallet(address)

        # Calculate component scores
        wealth_score = self._calculate_wealth_score(metrics)
        stability_score = self._calculate_stability_score(metrics)
        behavior_score = self._calculate_behavior_score(metrics)
        liquidity_score = self._calculate_liquidity_score(metrics)
        verification_score = self._calculate_verification_score(metrics)

        # Calculate weighted overall score
        overall_score = (
            wealth_score * self.WEALTH_WEIGHT +
            stability_score * self.STABILITY_WEIGHT +
            behavior_score * self.BEHAVIOR_WEIGHT +
            liquidity_score * self.LIQUIDITY_WEIGHT +
            verification_score * self.VERIFICATION_WEIGHT
        )

        scores = {
            "wealth": wealth_score,
            "stability": stability_score,
            "behavior": behavior_score,
            "liquidity": liquidity_score,
            "verification": verification_score
        }

        # Determine risk tier
        risk_tier = self._determine_risk_tier(overall_score, metrics)

        # Generate signals and flags
        positive_signals, risk_flags = self._generate_signals_and_flags(metrics, scores)

        # Estimate financials
        estimated_income = self._estimate_income(metrics)
        max_mortgage = self._calculate_max_mortgage(
            estimated_income, metrics.total_value_usd, risk_tier
        )
        recommended_ltv = self._recommend_ltv(risk_tier, metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, risk_tier, scores)

        # Identify contact methods
        contact_methods = self._identify_contact_methods(metrics)

        # Determine outreach priority
        outreach_priority = self._determine_outreach_priority(overall_score, metrics)

        return MortgageQualificationScore(
            wallet_address=address,
            overall_score=round(overall_score, 2),
            risk_tier=risk_tier.value,
            wealth_score=round(wealth_score, 2),
            stability_score=round(stability_score, 2),
            behavior_score=round(behavior_score, 2),
            liquidity_score=round(liquidity_score, 2),
            verification_score=round(verification_score, 2),
            estimated_annual_income=estimated_income,
            estimated_net_worth=metrics.total_value_usd,
            max_mortgage_amount=max_mortgage,
            recommended_ltv=recommended_ltv,
            positive_signals=positive_signals,
            risk_flags=risk_flags,
            recommendations=recommendations,
            contact_methods=contact_methods,
            outreach_priority=outreach_priority
        )

    def batch_analyze(self, addresses: List[str]) -> List[Dict]:
        """Analyze multiple wallets and return sorted by qualification score."""
        results = []

        for address in addresses:
            try:
                score = self.score_for_mortgage(address)
                results.append(asdict(score))
            except Exception as e:
                results.append({
                    "wallet_address": address,
                    "error": str(e),
                    "overall_score": 0
                })

        # Sort by overall score descending
        results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        return results

    def discover_prospects(self, min_value_usd: float = 50000,
                          min_score: float = 60,
                          sample_addresses: Optional[List[str]] = None) -> List[ProspectLead]:
        """
        Discover qualified prospects from a list of addresses.

        In production, this would integrate with:
        - Dune Analytics for whale discovery
        - Token holder lists from Etherscan
        - DeFi protocol user lists
        - NFT holder lists

        For demo, accepts a list of sample addresses to analyze.
        """
        prospects = []

        if not sample_addresses:
            return prospects

        for address in sample_addresses:
            try:
                metrics = self.analyze_wallet(address)

                # Filter by minimum value
                if metrics.total_value_usd < min_value_usd:
                    continue

                score = self.score_for_mortgage(address)

                # Filter by minimum score
                if score.overall_score < min_score:
                    continue

                lead = ProspectLead(
                    wallet_address=address,
                    qualification_score=score.overall_score,
                    risk_tier=score.risk_tier,
                    estimated_value=metrics.total_value_usd,
                    behavior_type=metrics.behavior_type,
                    contact_methods=score.contact_methods,
                    last_active=metrics.last_transaction_date or "unknown",
                    priority=score.outreach_priority,
                    notes=score.positive_signals[:3]  # Top 3 signals
                )
                prospects.append(lead)

            except Exception:
                continue

        # Sort by qualification score
        prospects.sort(key=lambda x: x.qualification_score, reverse=True)

        return prospects

    def generate_prospect_report(self, address: str) -> Dict:
        """Generate a comprehensive prospect report for a single wallet."""
        metrics = self.analyze_wallet(address)
        score = self.score_for_mortgage(address)

        return {
            "report_generated": datetime.now().isoformat(),
            "wallet_analysis": asdict(metrics),
            "qualification_score": asdict(score),
            "summary": {
                "qualified": score.risk_tier in ["prime", "near_prime"],
                "priority": score.outreach_priority,
                "estimated_opportunity": score.max_mortgage_amount,
                "key_strengths": score.positive_signals[:3],
                "key_concerns": score.risk_flags[:3],
                "next_steps": score.recommendations[:2]
            }
        }


# Demo/testing function
def demo_prospecting():
    """Demonstrate the prospecting service capabilities."""
    service = CryptoProspectingService()

    # Example: Analyze Vitalik's wallet (well-known public address)
    vitalik_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

    print("=== Crypto Mortgage Prospecting Tool Demo ===\n")
    print(f"Analyzing wallet: {vitalik_address}\n")

    # Generate full report
    report = service.generate_prospect_report(vitalik_address)

    print(f"Report Generated: {report['report_generated']}")
    print(f"\n--- Wallet Analysis ---")
    print(f"Total Value (USD): ${report['wallet_analysis']['total_value_usd']:,.2f}")
    print(f"ETH Balance: {report['wallet_analysis']['eth_balance']:.4f}")
    print(f"Wallet Age: {report['wallet_analysis']['wallet_age_days']} days")
    print(f"Behavior Type: {report['wallet_analysis']['behavior_type']}")

    print(f"\n--- Mortgage Qualification ---")
    print(f"Overall Score: {report['qualification_score']['overall_score']}/100")
    print(f"Risk Tier: {report['qualification_score']['risk_tier'].upper()}")
    print(f"Estimated Income: ${report['qualification_score']['estimated_annual_income']:,.0f}")
    print(f"Max Mortgage: ${report['qualification_score']['max_mortgage_amount']:,.0f}")
    print(f"Recommended LTV: {report['qualification_score']['recommended_ltv']}%")

    print(f"\n--- Outreach ---")
    print(f"Priority: {report['summary']['priority'].upper()}")
    print(f"Contact Methods: {len(report['qualification_score']['contact_methods'])}")

    return report


if __name__ == "__main__":
    demo_prospecting()
