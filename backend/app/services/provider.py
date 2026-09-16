import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.core.config import settings


class ProviderUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class PixChargeResult:
    provider: str
    provider_charge_id: str
    txid: str
    copy_paste: str


class PaymentProvider:
    name = "disabled"

    def create_pix_charge(
        self,
        *,
        amount: Decimal,
        reference: str | None,
        idempotency_key: str,
    ) -> PixChargeResult:
        raise ProviderUnavailable("Payment provider is disabled")


class MockPaymentProvider(PaymentProvider):
    name = "mock"

    def create_pix_charge(
        self,
        *,
        amount: Decimal,
        reference: str | None,
        idempotency_key: str,
    ) -> PixChargeResult:
        charge_id = f"mock_ch_{uuid.uuid5(uuid.NAMESPACE_URL, idempotency_key).hex}"
        txid = uuid.uuid5(uuid.NAMESPACE_OID, f"{idempotency_key}:{amount}").hex[:25]
        return PixChargeResult(
            provider=self.name,
            provider_charge_id=charge_id,
            txid=txid,
            copy_paste=f"MOCK-PIX-{txid}",
        )


def get_payment_provider() -> PaymentProvider:
    provider = settings.payment_provider.lower().strip()
    if provider == "mock":
        if settings.app_env.lower() == "production":
            raise ProviderUnavailable("Mock provider cannot run in production")
        return MockPaymentProvider()
    if provider == "disabled":
        return PaymentProvider()
    raise ProviderUnavailable(
        f"Provider '{provider}' is configured but no production adapter is installed"
    )
