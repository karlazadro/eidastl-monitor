from __future__ import annotations
from dataclasses import dataclass
from lxml import etree
import pandas as pd
import hashlib

@dataclass
class TLPointer:
    country_code: str
    tl_url: str

def _hash_key(*parts: str) -> str:
    joined = "|".join([p or "" for p in parts])
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()

def parse_lotl_for_pointers(lotl_xml_path: str) -> list[TLPointer]:
    tree = etree.parse(lotl_xml_path)
    root = tree.getroot()

    pointers: list[TLPointer] = []
    for p in root.xpath(".//*[local-name()='OtherTSLPointer']"):
        cc = p.xpath(".//*[local-name()='SchemeTerritory']/text()")
        cc = (cc[0].strip() if cc else "").upper()

        loc = p.xpath(".//*[local-name()='TSLLocation']/text()")
        loc = loc[0].strip() if loc else ""

        if cc and loc and loc.startswith("http") and len(cc) == 2:
            pointers.append(TLPointer(country_code=cc, tl_url=loc))

    dedup = {}
    for x in pointers:
        dedup[(x.country_code, x.tl_url)] = x
    return list(dedup.values())

def parse_trusted_list(tl_xml_path: str, country_code: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    tree = etree.parse(tl_xml_path)
    root = tree.getroot()

    providers_rows = []
    services_rows = []

    for tsp in root.xpath(".//*[local-name()='TrustServiceProvider']"):
        tsp_name = ""
        name_nodes = tsp.xpath(".//*[local-name()='TSPName']//*[local-name()='Name']/text()")
        if name_nodes:
            tsp_name = name_nodes[0].strip()

        tsp_uri = ""
        uri_nodes = tsp.xpath(".//*[local-name()='TSPInformationURI']//*[local-name()='URI']/text()")
        if uri_nodes:
            tsp_uri = uri_nodes[0].strip()

        provider_key = _hash_key(country_code, tsp_name, tsp_uri)

        providers_rows.append({
            "provider_key": provider_key,
            "country_code": country_code,
            "tsp_name": tsp_name,
            "tsp_uri": tsp_uri
        })

        for svc in tsp.xpath(".//*[local-name()='TSPService']"):
            svc_type = ""
            t_nodes = svc.xpath(".//*[local-name()='ServiceTypeIdentifier']/text()")
            if t_nodes:
                svc_type = t_nodes[0].strip()

            svc_name = ""
            sn_nodes = svc.xpath(".//*[local-name()='ServiceName']//*[local-name()='Name']/text()")
            if sn_nodes:
                svc_name = sn_nodes[0].strip()

            status = ""
            st_nodes = svc.xpath(".//*[local-name()='ServiceStatus']/text()")
            if st_nodes:
                status = st_nodes[0].strip()

            sst = ""
            sst_nodes = svc.xpath(".//*[local-name()='StatusStartingTime']/text()")
            if sst_nodes:
                sst = sst_nodes[0].strip()

            service_key = _hash_key(country_code, provider_key, svc_type, svc_name)

            services_rows.append({
                "service_key": service_key,
                "provider_key": provider_key,
                "country_code": country_code,
                "service_type_identifier": svc_type,
                "service_name": svc_name,
                "current_status": status,
                "status_starting_time": sst
            })

    providers_df = pd.DataFrame(providers_rows).drop_duplicates(subset=["provider_key"])
    services_df = pd.DataFrame(services_rows).drop_duplicates(subset=["service_key"])
    return providers_df, services_df
