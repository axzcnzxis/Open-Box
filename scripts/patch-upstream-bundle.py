#!/usr/bin/env python3
import sys
import tarfile
import io
import hashlib
import json

def patch_tarball(tar_path):
    print(f'==> Patching {tar_path}...')
    with tarfile.open(tar_path, 'r:gz') as tar_in:
        members = tar_in.getmembers()
        files = {}
        for m in members:
            if m.isfile():
                files[m.name] = tar_in.extractfile(m).read()

    # 1. Patch openwrt/initd/openbox (Disable proxy conflict refusal)
    if 'openwrt/initd/openbox' in files:
        initd = files['openwrt/initd/openbox'].decode('utf-8', errors='ignore')
        if 'openbox_refuse_if_conflict() {' in initd:
            s_idx = initd.find('openbox_refuse_if_conflict() {')
            e_idx = initd.find('start_service() {', s_idx)
            new_refuse = 'openbox_refuse_if_conflict() {\n\treturn 0\n}\n\n'
            files['openwrt/initd/openbox'] = (initd[:s_idx] + new_refuse + initd[e_idx:]).encode('utf-8')
            print('  [+] Patched openwrt/initd/openbox')

    # 2. Patch panel/server/index.mjs (Disable backend conflict checks & auto-stop)
    if 'panel/server/index.mjs' in files:
        idx_mjs = files['panel/server/index.mjs'].decode('utf-8', errors='ignore')
        if 'ca=async e=>' in idx_mjs:
            ca_start = idx_mjs.find('ca=async e=>{')
            if ca_start != -1:
                ca_end = idx_mjs.find('return{conflicts:t,hasRunning:t.length>0}}', ca_start) + len('return{conflicts:t,hasRunning:t.length>0}}')
                idx_mjs = idx_mjs[:ca_start] + 'ca=async e=>({conflicts:[],hasRunning:!1})' + idx_mjs[ca_end:]

        idx_mjs = idx_mjs.replace('let i=await Ih(t);', 'let i=[];')
        idx_mjs = idx_mjs.replace(',_)return{ok:!1,stage:"conflict",message:Ph(S)};', ';')
        files['panel/server/index.mjs'] = idx_mjs.encode('utf-8')
        print('  [+] Patched panel/server/index.mjs')

    # 3. Patch panel/server/cli/deploy.mjs (Disable CLI conflict checks)
    if 'panel/server/cli/deploy.mjs' in files:
        dep_mjs = files['panel/server/cli/deploy.mjs'].decode('utf-8', errors='ignore')
        if 'tc=async e=>' in dep_mjs:
            tc_start = dep_mjs.find('tc=async e=>{')
            if tc_start != -1:
                tc_end = dep_mjs.find('return{conflicts:t,hasRunning:t.length>0}}', tc_start) + len('return{conflicts:t,hasRunning:t.length>0}}')
                dep_mjs = dep_mjs[:tc_start] + 'tc=async e=>({conflicts:[],hasRunning:!1})' + dep_mjs[tc_end:]

        dep_mjs = dep_mjs.replace(',w)return{ok:!1,stage:"conflict",message:ec(A)};', ';')
        files['panel/server/cli/deploy.mjs'] = dep_mjs.encode('utf-8')
        print('  [+] Patched panel/server/cli/deploy.mjs')

    # 4. Patch tutorial-videos.json
    if 'panel/server/defaults/tutorial-videos.json' in files:
        files['panel/server/defaults/tutorial-videos.json'] = json.dumps({'videos': []}, indent=2).encode('utf-8')
        print('  [+] Cleaned panel/server/defaults/tutorial-videos.json')

    # 5. Patch panel/dist/assets/index-BvJDWHo_.js (Remove MarketLink & ad banners)
    if 'panel/dist/assets/index-BvJDWHo_.js' in files:
        fe = files['panel/dist/assets/index-BvJDWHo_.js'].decode('utf-8', errors='ignore')
        my_start = fe.find('my=ye({__name:"MarketLink"')
        if my_start != -1:
            my_end = fe.find('Cge))}})', my_start) + len('Cge))}})')
            new_my = 'my=ye({__name:"MarketLink",props:{icon:{type:Boolean,default:!1}},setup(e){return(t,n)=>(b(),w("span",{class:"hidden"}))}})'
            fe = fe[:my_start] + new_my + fe[my_end:]

        promo_start = fe.find('L(Eo)||L(hU)?(b(),w(X,{key:1}')
        if promo_start != -1:
            promo_end = fe.find(')):V("",!0)', promo_start) + len(')):V("",!0)')
            fe = fe[:promo_start] + 'V("",!0)' + fe[promo_end:]

        fe = fe.replace('https://blog.angeworld.cc/market', '#')
        fe = fe.replace('https://ai.superdoor.top', '#')
        fe = fe.replace('https://ai.opendoor.sbs/', '#')
        files['panel/dist/assets/index-BvJDWHo_.js'] = fe.encode('utf-8')
        print('  [+] Patched panel/dist/assets/index-BvJDWHo_.js')

    # 6. Patch panel/dist/assets/index-Bemk_BEs.js (Remove market/promo text)
    if 'panel/dist/assets/index-Bemk_BEs.js' in files:
        i18n = files['panel/dist/assets/index-Bemk_BEs.js'].decode('utf-8', errors='ignore')
        i18n = i18n.replace('marketName:"AnGe Market"', 'marketName:""')
        i18n = i18n.replace('subscriptionEmptyHint:"No subscriptions yet \u2014 grab one from"', 'subscriptionEmptyHint:"No subscriptions yet"')
        i18n = i18n.replace('subscriptionEmptyHintSuffix:"?"', 'subscriptionEmptyHintSuffix:""')
        i18n = i18n.replace('chainProxyEmptyHint:"No residential IP yet? Get one from"', 'chainProxyEmptyHint:"No residential IP yet"')
        i18n = i18n.replace('marketName:"安格超市"', 'marketName:""')
        i18n = i18n.replace('subscriptionEmptyHint:"还没有订阅，去"', 'subscriptionEmptyHint:"还没有订阅"')
        i18n = i18n.replace('subscriptionEmptyHintSuffix:"买一个？"', 'subscriptionEmptyHintSuffix:""')
        i18n = i18n.replace('chainProxyEmptyHint:"没有住宅 IP？去"', 'chainProxyEmptyHint:"没有住宅 IP"')
        i18n = i18n.replace('chainProxyEmptyHintSuffix:"买一个"', 'chainProxyEmptyHintSuffix:""')
        files['panel/dist/assets/index-Bemk_BEs.js'] = i18n.encode('utf-8')
        print('  [+] Patched panel/dist/assets/index-Bemk_BEs.js')

    # 7. Update panel/server/hardening-manifest.json SHA256 checksums
    if 'panel/server/hardening-manifest.json' in files:
        manifest = json.loads(files['panel/server/hardening-manifest.json'].decode('utf-8'))
        for filepath in manifest.get('files', {}):
            full_path = f'panel/server/{filepath}'
            if full_path in files:
                new_hash = hashlib.sha256(files[full_path]).hexdigest()
                manifest['files'][filepath] = new_hash
        files['panel/server/hardening-manifest.json'] = json.dumps(manifest, indent=2).encode('utf-8')
        print('  [+] Updated panel/server/hardening-manifest.json checksums')

    # Repack tarball
    with tarfile.open(tar_path, 'w:gz') as tar_out:
        for m in members:
            if m.isfile():
                data = files[m.name]
                ti = tarfile.TarInfo(name=m.name)
                ti.size = len(data)
                ti.mode = m.mode
                ti.mtime = m.mtime
                ti.type = m.type
                ti.uid = m.uid
                ti.gid = m.gid
                ti.uname = m.uname
                ti.gname = m.gname
                tar_out.addfile(ti, io.BytesIO(data))
            else:
                tar_out.addfile(m)
    print(f'==> Finished {tar_path}')

if __name__ == '__main__':
    for path in sys.argv[1:]:
        patch_tarball(path)
