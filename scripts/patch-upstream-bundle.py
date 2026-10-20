#!/usr/bin/env python3
import sys
import tarfile
import io
import hashlib
import json
import re

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

    # 2. Patch openwrt/bin/open-box and Luci view (Replace repo and port)
    if 'openwrt/bin/open-box' in files:
        ob = files['openwrt/bin/open-box'].decode('utf-8', errors='ignore')
        ob = ob.replace('REPO="liandu2024/Open-Box"', 'REPO="axzcnzxis/Open-Box"')
        ob = ob.replace('7891', '7894')
        files['openwrt/bin/open-box'] = ob.encode('utf-8')
        print('  [+] Patched openwrt/bin/open-box')

    if 'openwrt/luci/htdocs/luci-static/resources/view/openbox/main.js' in files:
        lucim = files['openwrt/luci/htdocs/luci-static/resources/view/openbox/main.js'].decode('utf-8', errors='ignore')
        lucim = lucim.replace("REPO = 'liandu2024/Open-Box'", "REPO = 'axzcnzxis/Open-Box'")
        files['openwrt/luci/htdocs/luci-static/resources/view/openbox/main.js'] = lucim.encode('utf-8')
        print('  [+] Patched luci main.js')

    # 3. Patch panel/server/index.mjs
    if 'panel/server/index.mjs' in files:
        idx_mjs = files['panel/server/index.mjs'].decode('utf-8', errors='ignore')

        # Replace upstream repo for updates
        idx_mjs = idx_mjs.replace('"liandu2024/Open-Box"', '"axzcnzxis/Open-Box"')

        # Change inbound port 7891 -> 7894 (Method 2)
        idx_mjs = idx_mjs.replace('7891,Vi="panel-in"', '7894,Vi="panel-in"')
        idx_mjs = idx_mjs.replace('7853,7891,53,22', '7853,7894,53,22')

        # Disable conflict checks
        if 'hasRunning:t.length>0}}' in idx_mjs:
            c_idx = idx_mjs.find('hasRunning:t.length>0}}')
            # find start of pa=async e=>{
            fn_start = idx_mjs.rfind('async e=>{', 0, c_idx)
            fn_name_start = idx_mjs.rfind('=', 0, fn_start)
            idx_mjs = idx_mjs[:fn_name_start+1] + 'async e=>({conflicts:[],hasRunning:!1})' + idx_mjs[c_idx + len('hasRunning:t.length>0}}'):]

        # In index.mjs, conflict check abort:
        # replace: if($("冲突检测"),_)return{ok:!1,stage:"conflict",message:Dh(E)};
        idx_mjs = re.sub(r'if\(\$\("[^"]*"\),_\)return\{ok:!1,stage:"conflict",message:[^}]+\};', '', idx_mjs)
        # replace auto-stop:
        idx_mjs = idx_mjs.replace('let a=Ih(i),c=await n();', 'let a=Ih([]),c=await n();')

        files['panel/server/index.mjs'] = idx_mjs.encode('utf-8')
        print('  [+] Patched panel/server/index.mjs')

    # 4. Patch panel/server/cli/deploy.mjs
    if 'panel/server/cli/deploy.mjs' in files:
        dep_mjs = files['panel/server/cli/deploy.mjs'].decode('utf-8', errors='ignore')

        # Change inbound port 7891 -> 7894 (Method 2)
        dep_mjs = dep_mjs.replace('7853,7891,53,22', '7853,7894,53,22')

        # Disable CLI conflict checks
        if 'hasRunning:t.length>0}}' in dep_mjs:
            c_idx = dep_mjs.find('hasRunning:t.length>0}}')
            fn_start = dep_mjs.rfind('async e=>{', 0, c_idx)
            fn_name_start = dep_mjs.rfind('=', 0, fn_start)
            dep_mjs = dep_mjs[:fn_name_start+1] + 'async e=>({conflicts:[],hasRunning:!1})' + dep_mjs[c_idx + len('hasRunning:t.length>0}}'):]

        # replace: if($("冲突检测"),k)return{ok:!1,stage:"conflict",message:ac(A)};
        dep_mjs = re.sub(r'if\(\$\("[^"]*"\),[a-zA-Z0-9_$]+\)return\{ok:!1,stage:"conflict",message:[^}]+\};', '', dep_mjs)

        files['panel/server/cli/deploy.mjs'] = dep_mjs.encode('utf-8')
        print('  [+] Patched panel/server/cli/deploy.mjs')

    # 5. Patch tutorial-videos.json
    if 'panel/server/defaults/tutorial-videos.json' in files:
        files['panel/server/defaults/tutorial-videos.json'] = json.dumps({'videos': []}, indent=2).encode('utf-8')
        print('  [+] Cleaned panel/server/defaults/tutorial-videos.json')

    # 6. Patch frontend JS assets in panel/dist/assets/
    for fname in list(files.keys()):
        if fname.startswith('panel/dist/assets/') and fname.endswith('.js'):
            fe = files[fname].decode('utf-8', errors='ignore')
            modified = False

            # Replace repo URLs
            if 'liandu2024/Open-Box' in fe:
                fe = fe.replace('liandu2024/Open-Box', 'axzcnzxis/Open-Box')
                modified = True

            # Remove YouTube tutorial button
            # p("button",{type:"button",class:"hover:bg-base-200 inline-flex cursor-pointer items-center gap-2 rounded-lg py-1",onClick:m[0]||(m[0]=S=>o.value=!0)},[O(Ra,{code:"brand:youtube",size:20}),p("span",Y5e,x(g.$t("tutorialButton")),1)])
            # YouTube tutorial button
            yt_btn = 'brand:youtube",size:20}),p("span",Y5e,x(g.$t("tutorialButton")),1)])'
            if yt_btn in fe:
                idx = fe.find(yt_btn)
                btn_start = fe.rfind('p("button",', 0, idx)
                if btn_start != -1:
                    btn_end = idx + len(yt_btn)
                    fe = fe[:btn_start] + 'V("",!0)' + fe[btn_end:]
                    modified = True
                    print(f'  [+] Removed YouTube tutorial button from {fname}')

            # Remove promo banners & MarketLink
            if '__name:"MarketLink"' in fe:
                my_start = fe.find('ye({__name:"MarketLink"')
                if my_start != -1:
                    setup_idx = fe.find('setup(e){', my_start)
                    ret_idx = fe.find('return', setup_idx)
                    close_idx = fe.find('}})', ret_idx)
                    new_setup = 'return(t,n)=>(b(),w("span",{class:"hidden"}))'
                    fe = fe[:ret_idx] + new_setup + fe[close_idx:]
                    modified = True

            # Promo banner
            promo_match = re.search(r'L\([a-zA-Z0-9_$]+\)\|\|L\([a-zA-Z0-9_$]+\)\?\(b\(\),w\(X,\{key:1\}.*?\)\):V\("",!0\)', fe)
            if promo_match:
                fe = fe[:promo_match.start()] + 'V("",!0)' + fe[promo_match.end():]
                modified = True

            fe = fe.replace('https://blog.angeworld.cc/market', '#')
            fe = fe.replace('https://ai.superdoor.top', '#')
            fe = fe.replace('https://ai.opendoor.sbs/', '#')

            if modified:
                files[fname] = fe.encode('utf-8')
                print(f'  [+] Patched frontend asset: {fname}')

        elif fname.startswith('panel/dist/assets/') and fname.endswith('.css'):
            pass

    # 7. Update panel/server/hardening-manifest.json and openbox-core binary SHA256 checksums
    if 'panel/server/hardening-manifest.json' in files and 'panel/server/native/openbox-core' in files:
        manifest = json.loads(files['panel/server/hardening-manifest.json'].decode('utf-8'))
        core_binary = bytearray(files['panel/server/native/openbox-core'])
        
        for filepath, old_hash in manifest.get('files', {}).items():
            full_path = f'panel/server/{filepath}'
            if full_path in files:
                new_hash = hashlib.sha256(files[full_path]).hexdigest()
                manifest['files'][filepath] = new_hash
                
                # Replace in openbox-core binary
                old_bytes = old_hash.encode('ascii')
                new_bytes = new_hash.encode('ascii')
                if old_bytes in core_binary:
                    core_binary = bytearray(bytes(core_binary).replace(old_bytes, new_bytes))
                    print(f'  [+] Replaced SHA256 in openbox-core for {filepath}')
                else:
                    print(f'  [-] SHA256 for {filepath} not found in openbox-core (may not be verified)')

        files['panel/server/native/openbox-core'] = bytes(core_binary)
        # Update manifest hash for core binary itself
        manifest['files']['native/openbox-core'] = hashlib.sha256(files['panel/server/native/openbox-core']).hexdigest()
        files['panel/server/hardening-manifest.json'] = json.dumps(manifest, indent=2).encode('utf-8')
        print('  [+] Updated panel/server/hardening-manifest.json & openbox-core')

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
