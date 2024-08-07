"""Device registration assertions and actions"""
import logging
import secrets
import time
from dataclasses import dataclass
from typing import Optional
from c8y_test_core.assert_device import AssertDevice
from c8y_test_core.utils import to_csv


@dataclass
class DeviceCredentials:
    """Device credentials"""

    username: str
    password: str


log = logging.getLogger()


class AssertDeviceRegistration(AssertDevice):
    """Assertions"""

    def bulk_register_with_basic_auth(
        self,
        external_id: str,
        external_type: Optional[str] = "c8y_Serial",
        name: Optional[str] = None,
        device_type: Optional[str] = "thin-edge.io",
        **kwargs,
    ) -> DeviceCredentials:
        """Bulk device registration for device that require
        non-cert based authentication (e.g. basic auth)

        Arguments:
            external_id (str): External id
            external_type (str): External type. Defaults to c8y_Serial
            name (Optional[str]): Name of the device. Defaults to the external_id
            type (Optional[str]): Type of the device. Defaults to thin-edge.io
        """
        name = name or external_id
        password = secrets.token_urlsafe(14)
        symbols = "".join([secrets.choice(".$-?@!") for i in range(0, 2)])
        password = password + symbols

        registration_body = to_csv(
            [
                ("ID", [external_id]),
                ("IDTYPE", [external_type]),
                ("AUTH_TYPE", ["BASIC"]),
                ("CREDENTIALS", [password]),
                ("TYPE", [device_type]),
                ("NAME", [name]),
                ("com_cumulocity_model_Agent.active", [True]),
            ]
        )

        resp = self.context.client.post_file(
            "/devicecontrol/bulkNewDeviceRequests",
            registration_body.encode("utf-8"),
            accept="application/json",
        )
        log.info("Registration response: %s", resp)
        assert resp["numberOfSuccessful"] == resp["numberOfAll"], (
            "Failed to register device\n" f"response:\n{resp}"
        )

        username = f"device_{external_id}"
        if self.context.client.tenant_id:
            username = f"{self.context.client.tenant_id}/device_{external_id}"

        return DeviceCredentials(username, password)

    def register_with_basic_auth(self, external_id: str, timeout: float = 60, **kwargs):
        """Register a single device using the basic auth

        For the registration to work, the device must be polling the
        POST /devicecontrol/newDeviceRequests/{external_id} endpoint in the background.
        Once the request is approved by this function, the device will receive
        platform credentials.

        Arguments:
            external_id (str): external id of the device to be registered
            timeout (float): Timeout in seconds. Defaults to 60
        """
        resp = self.context.client.post(
            "/devicecontrol/newDeviceRequests",
            json={
                "id": external_id,
            },
            accept="application/json",
        )
        log.info("Registration response. %s", resp)

        # pylint: disable=broad-exception-caught
        success = False
        timeout_at = time.monotonic() + timeout
        while True:
            try:
                resp = self.context.client.put(
                    f"/devicecontrol/newDeviceRequests/{external_id}",
                    json={
                        "status": "ACCEPTED",
                    },
                    accept="application/json",
                    content_type="application/json",
                )
                log.info("Registration accepted: %s", resp)
                success = True
                break
            except Exception as ex:
                log.info(
                    "Registration accepted failed: response=%s, exception=%s", resp, ex
                )
            time.sleep(3)
            if time.monotonic() > timeout_at:
                break

        assert success, "Failed to register device"
