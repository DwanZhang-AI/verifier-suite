"""Original Gavel Docker provider, with scoped private capability/network mounts."""
import json,shlex
from urllib.parse import urlsplit
from config import load,paths
from local_docker_provider import LocalDockerEnvironment
from harbor.models.task.config import NetworkMode

class VGBEnvironment(LocalDockerEnvironment):
    def validate_network_policy_support(self,network_policy=None):
        cfg=load();policy=network_policy or self._network_policy
        if policy.network_mode!=NetworkMode.ALLOWLIST or set(policy.allowed_hosts)!={urlsplit(cfg['api_base_url']).hostname}:raise ValueError('Only configured model endpoint is allowed')
    def _ensure_airgap_sync(self):
        from network import check_private,check_proxy
        cfg=load();w,_,_,_=paths(cfg);receipt=json.loads((w/'private-network.json').read_text())
        n=json.loads(self._run('docker network inspect '+shlex.quote(cfg['private_network']),name='vgb-net-check'))[0]
        subnet,gateway=check_private(cfg,n)
        if subnet!=receipt['subnet'] or gateway!=receipt['gateway']:raise RuntimeError('Private network address changed')
        c=json.loads(self._run('docker container inspect '+shlex.quote(receipt['proxy_container']),name='vgb-proxy-check'))[0]
        if not check_proxy(cfg,c)['running']:raise RuntimeError('Model proxy is not running on the private network')
    def _net_flags(self):
        cfg=load();_,a,_,_=paths(cfg)
        # Without NET_RAW a task container cannot craft frames toward the host's other addresses.
        flags='--network '+shlex.quote(cfg['private_network'])+' --cap-drop NET_RAW --memory 2g --cpus 1 '
        cap=a/'cap-rpc'/self.environment_name
        if cap.is_dir():flags+='--mount '+shlex.quote('type=bind,src='+str(cap)+',dst=/vgb-cap')+' '
        return flags
