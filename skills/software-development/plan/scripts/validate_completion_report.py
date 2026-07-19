#!/usr/bin/env python3
"""Validate a plan completion report. Owner: SKILL.md PD-006; contract: references/execution-ready-plan-contract.md."""
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path
from typing import Any
PASS = "PASS"
CHECKS = ("all_requirements_pass", "all_required_validators_pass", "all_required_artifacts_exist", "all_changed_files_accounted_for", "all_required_gates_pass", "all_blockers_closed", "no_unapproved_scope_change", "human_and_machine_reports_match", "rollback_and_cleanup_complete", "independent_review_pass")
SHAPES = {
 "baselines": {"id", "method", "expected_exit_code", "actual_exit_code", "known_failure_signature", "evidence_ids"},
 "tasks": {"id", "requirement_ids", "artifact_ids", "evidence_ids", "status"},
 "requirements": {"id", "status", "task_ids", "validator_ids", "evidence_ids", "waiver_id"},
 "validators": {"id", "requirement_ids", "task_ids", "scope", "method", "working_directory", "expected_exit_code", "actual_exit_code", "pass_condition", "actual_result", "evidence_ids", "status"},
 "gates": {"id", "type", "task_ids", "validator_ids", "evidence_ids", "status", "owner"},
 "risks": {"id", "task_ids", "gate_ids", "evidence_ids", "status", "prevention_evidence", "detection_evidence", "response_or_rollback_evidence", "owner"},
 "changed_files": {"id", "path", "task_id", "artifact_ids", "evidence_ids", "expected"},
 "artifacts": {"id", "task_id", "evidence_ids", "path", "sha256", "required", "exists"},
 "evidence": {"id", "validator_id", "kind", "check_names", "covers_ids", "path", "sha256"},
 "waivers": {"id", "scope_ids", "approver", "reason", "expires_or_revisit", "remaining_risk"},
 "residual_risks": {"id", "risk_id", "description", "owner", "accepted_by", "revisit_condition", "evidence_ids"},
 "cleanup": {"id", "action", "result", "evidence_ids", "status"},
 "reviews": {"id", "type", "evidence_ids", "status"},
}
PREFIX = {"baselines":"BASE", "tasks":"TASK", "requirements":"REQ", "validators":"VAL", "gates":"GATE", "risks":"RISK", "changed_files":"FILE", "artifacts":"ART", "evidence":"EVID", "waivers":"WAIVER", "residual_risks":"RESIDUAL", "cleanup":"CLEAN", "reviews":"REVIEW"}
LINKS = {"baselines":{"evidence_ids":"evidence"}, "tasks":{"requirement_ids":"requirements", "artifact_ids":"artifacts", "evidence_ids":"evidence"}, "requirements":{"task_ids":"tasks", "validator_ids":"validators", "evidence_ids":"evidence"}, "validators":{"requirement_ids":"requirements", "task_ids":"tasks", "evidence_ids":"evidence"}, "gates":{"task_ids":"tasks", "validator_ids":"validators", "evidence_ids":"evidence"}, "risks":{"task_ids":"tasks", "gate_ids":"gates", "evidence_ids":"evidence"}, "changed_files":{"artifact_ids":"artifacts", "evidence_ids":"evidence"}, "artifacts":{"evidence_ids":"evidence"}, "residual_risks":{"evidence_ids":"evidence"}, "cleanup":{"evidence_ids":"evidence"}, "reviews":{"evidence_ids":"evidence"}}
TEXT = {"baselines":("method", "known_failure_signature"), "validators":("method", "working_directory", "pass_condition", "actual_result"), "gates":("owner",), "risks":("prevention_evidence", "detection_evidence", "response_or_rollback_evidence", "owner"), "changed_files":("path",), "cleanup":("action", "result"), "waivers":("approver", "reason", "expires_or_revisit", "remaining_risk"), "residual_risks":("description", "owner", "accepted_by", "revisit_condition")}
KINDS = {"all_requirements_pass":{"command","report"}, "all_required_validators_pass":{"command","report"}, "all_required_artifacts_exist":{"artifact","report"}, "all_changed_files_accounted_for":{"command","report"}, "all_required_gates_pass":{"command","approval","report"}, "all_blockers_closed":{"report"}, "no_unapproved_scope_change":{"approval","report"}, "human_and_machine_reports_match":{"report"}, "rollback_and_cleanup_complete":{"recovery","report"}, "independent_review_pass":{"review"}}
TOP = {"_meta", "plan", "source_snapshot", *SHAPES, "blockers", "human_report", "checks", "check_evidence"}; MAX_EVIDENCE_BYTES = 10_000_000
def _text(value: Any) -> bool: return isinstance(value, str) and bool(value.strip())
def _list(value: Any) -> list[Any]: return value if isinstance(value,list) else []
def _shape(item: Any, keys: set[str], label: str, errors: list[str]) -> bool: valid=isinstance(item,dict) and set(item)==keys; errors.extend([] if valid else [f"{label} has invalid keys"]); return valid
def _ident(value: Any, prefix: str) -> bool: return _text(value) and re.fullmatch(rf"{prefix}-[0-9]{{3}}", value) is not None
def _strings(value: Any, prefix: str, label: str, errors: list[str]) -> list[str]:
 if not isinstance(value, list) or not value or any(not _ident(item, prefix) for item in value): errors.append(f"{label} must contain {prefix}-### ids"); return []
 if len(value) != len(set(value)): errors.append(f"{label} has duplicate ids")
 return value
def _records(report: dict[str, Any], errors: list[str]) -> tuple[dict[str,list[dict[str,Any]]],dict[str,set[str]]]:
 groups: dict[str,list[dict[str,Any]]] = {}; ids: dict[str,set[str]] = {}
 for name, shape in SHAPES.items():
  raw=report.get(name); allowed_empty=name in {"waivers", "residual_risks"}
  if not isinstance(raw,list) or (not raw and not allowed_empty): errors.append(f"{name} must be {'a' if allowed_empty else 'a nonempty'} list"); raw=[]
  groups[name]=[item for item in raw if _shape(item,shape,f"{name} entry",errors)]
  values=[item.get("id") for item in groups[name]]
  if any(not _ident(value,PREFIX[name]) for value in values) or len(values)!=len(set(values)): errors.append(f"{name} ids are invalid or duplicate"); values=[]
  ids[name]=set(values)
 all_ids=[value for values in ids.values() for value in values]
 if len(all_ids)!=len(set(all_ids)): errors.append("ids must be unique across collections")
 return groups,ids
def _links(groups: dict[str,list[dict[str,Any]]], ids: dict[str,set[str]], errors: list[str]) -> None:
 for name,config in LINKS.items():
  for item,(key,target) in itertools.product(groups[name],config.items()):
    values=_strings(item.get(key),PREFIX[target],f"{name}:{item.get('id')} {key}",errors)
    if not set(values)<=ids[target]: errors.append(f"{name}:{item.get('id')} has unknown {key}")
 for name,fields in TEXT.items():
  for item in groups[name]:
   if any(not _text(item.get(field)) for field in fields): errors.append(f"{name}:{item.get('id')} lacks required text")
def _header(report: dict[str,Any], errors: list[str]) -> None:
 if set(report)!=TOP: errors.append("top-level keys do not match the contract")
 meta=report.get("_meta"); meta_keys={"contract","validator","report_purpose","path_rule","evidence_file_rule","human_report_rule","plan_status_values","requirement_status_values","required_item_status_values","risk_status_values","validator_scope_values","evidence_kind_values","gate_type_values","id_format"}
 if not _shape(meta,meta_keys,"_meta",errors): meta={}
 expected={"contract":"../references/execution-ready-plan-contract.md","validator":"../scripts/validate_completion_report.py","report_purpose":"Copy this file into a plan-owned report path and replace every placeholder with fresh execution evidence.","path_rule":"Resolve normalized artifact, evidence, and human-report paths within the completion-report directory; reject absolute paths, escapes, and symlink escapes.","evidence_file_rule":"Each evidence file is JSON that exactly matches its evidence metadata and producing validator result.","human_report_rule":"The human report is JSON containing exactly plan_id, status, checks, and check_evidence from this machine report.","plan_status_values":["PASS","BLOCKED"],"requirement_status_values":["PASS","BLOCKED","WAIVED"],"required_item_status_values":["PASS","BLOCKED"],"risk_status_values":["open","mitigated","accepted"],"validator_scope_values":["task-local","whole-plan"],"evidence_kind_values":["command","artifact","review","approval","recovery","report"],"gate_type_values":["pre-flight","revision","escalation","abort","approval"],"id_format":"TYPE-###"}
 if any(meta.get(key)!=value for key,value in expected.items()): errors.append("_meta values do not match the contract")
 plan=report.get("plan"); keys={"id","path","status","started_at","completed_at","status_reason"}
 if not _shape(plan,keys,"plan",errors): plan={}
 if not _ident(plan.get("id"),"PLAN") or plan.get("status")!=PASS or any(not _text(plan.get(key)) for key in keys-{"id","status"}): errors.append("plan is incomplete or not PASS")
 sources=report.get("source_snapshot")
 if not isinstance(sources,list) or not sources: errors.append("source_snapshot must be a nonempty list"); sources=[]
 for item in sources:
  if not _shape(item,{"path_or_url","sha256_or_version","status"},"source_snapshot entry",errors) or item.get("status")!="verified" or not _text(item.get("path_or_url")) or not _text(item.get("sha256_or_version")): errors.append("source_snapshot entry is not verified")
 if report.get("blockers")!=[]: errors.append("blockers must be empty")
def _statuses(groups: dict[str,list[dict[str,Any]]], ids: dict[str,set[str]], errors: list[str]) -> None:
 for name in ("tasks","validators","gates","cleanup","reviews"):
  for item in groups[name]:
   if item.get("status")!=PASS: errors.append(f"{name}:{item.get('id')} must PASS")
 for item in groups["risks"]:
  if not _text(item.get("status")) or item.get("status") not in {"mitigated","accepted"}: errors.append(f"risks:{item.get('id')} must be mitigated or accepted")
 for item in groups["validators"]:
  if not _text(item.get("scope")) or item.get("scope") not in {"task-local","whole-plan"} or type(item.get("expected_exit_code")) is not int or type(item.get("actual_exit_code")) is not int or item.get("actual_exit_code")!=item.get("expected_exit_code"): errors.append(f"validators:{item.get('id')} has invalid scope or result")
 for item in groups["gates"]:
  if not _text(item.get("type")) or item.get("type") not in {"pre-flight","revision","escalation","abort","approval"}: errors.append(f"gates:{item.get('id')} has invalid type")
 for item in groups["changed_files"]:
  task_id=item.get("task_id")
  if item.get("expected") is not True or not _ident(task_id,"TASK") or task_id not in ids["tasks"]: errors.append(f"changed_files:{item.get('id')} is unexpected or has invalid task_id")
 for item in groups["artifacts"]:
  task_id=item.get("task_id")
  if item.get("required") is not True or item.get("exists") is not True or not _ident(task_id,"TASK") or task_id not in ids["tasks"]: errors.append(f"artifacts:{item.get('id')} is missing or has invalid task_id")
 for item in groups["evidence"]:
  if not _text(item.get("kind")) or item.get("kind") not in {"command","artifact","review","approval","recovery","report"} or not isinstance(checks:=item.get("check_names"),list) or not checks or any(not _text(value) or value not in CHECKS for value in checks) or len(checks)!=len(set(checks)): errors.append(f"evidence:{item.get('id')} has invalid kind or check_names")
 for item in groups["reviews"]:
  if not _text(item.get("type")) or item.get("type") not in {"spec","quality","independent"}: errors.append(f"reviews:{item.get('id')} has invalid type")
def _graph(groups: dict[str,list[dict[str,Any]]], ids: dict[str,set[str]], plan_id: str, report_id: str, errors: list[str]) -> None:
 req={item["id"]:item for item in groups["requirements"] if _ident(item.get("id"),"REQ")}; tasks={item["id"]:item for item in groups["tasks"] if _ident(item.get("id"),"TASK")}; vals={item["id"]:item for item in groups["validators"] if _ident(item.get("id"),"VAL")}; arts={item["id"]:item for item in groups["artifacts"] if _ident(item.get("id"),"ART")}; evid={item["id"]:item for item in groups["evidence"] if _ident(item.get("id"),"EVID")}; records={item["id"]:item for name in LINKS for item in groups[name] if _ident(item.get("id"),PREFIX[name])}
 for item in groups["tasks"]:
  for linked in _list(item.get("requirement_ids")):
   if not _ident(linked,"REQ") or item.get("id") not in _list(req.get(linked,{}).get("task_ids")): errors.append(f"tasks:{item.get('id')} lacks reciprocal requirement link")
  for linked in _list(item.get("artifact_ids")):
   if not _ident(linked,"ART") or arts.get(linked,{}).get("task_id")!=item.get("id"): errors.append(f"tasks:{item.get('id')} lacks reciprocal artifact link")
 for item in groups["validators"]:
  for linked in _list(item.get("requirement_ids")):
   if not _ident(linked,"REQ") or item.get("id") not in _list(req.get(linked,{}).get("validator_ids")): errors.append(f"validators:{item.get('id')} lacks reciprocal requirement link")
 for item in groups["requirements"]:
  task_ids=_list(item.get("task_ids")); validator_ids=_list(item.get("validator_ids"))
  if any(not _ident(link,"TASK") or item.get("id") not in _list(tasks.get(link,{}).get("requirement_ids")) for link in task_ids) or any(not _ident(link,"VAL") or item.get("id") not in _list(vals.get(link,{}).get("requirement_ids")) for link in validator_ids): errors.append(f"requirements:{item.get('id')} lacks reciprocal links")
 valid=set().union(*ids.values(),{plan_id,report_id})
 for item in groups["evidence"]:
  covers=_strings(item.get("covers_ids"),"[A-Z]+",f"evidence:{item.get('id')} covers_ids",errors); validator_id=item.get("validator_id")
  if not set(covers)<=valid or not _ident(validator_id,"VAL") or validator_id not in ids["validators"] or item.get("id") not in _list(vals.get(validator_id,{}).get("evidence_ids")) or any(covered in records and item.get("id") not in _list(records[covered].get("evidence_ids")) for covered in covers): errors.append(f"evidence:{item.get('id')} has invalid or nonreciprocal provenance")
 for name in LINKS:
  for item in groups[name]:
   raw=item.get("evidence_ids"); linked=raw if isinstance(raw,list) else []
   if any(not _ident(value,"EVID") or item.get("id") not in _list(evid.get(value,{}).get("covers_ids")) for value in linked): errors.append(f"{name}:{item.get('id')} lacks evidence coverage")
 for item in groups["validators"]:
  linked=_list(item.get("evidence_ids"))
  if any(not _ident(value,"EVID") or evid.get(value,{}).get("validator_id")!=item.get("id") for value in linked): errors.append(f"validators:{item.get('id')} has foreign evidence")
def _waivers(groups: dict[str,list[dict[str,Any]]], ids: dict[str,set[str]], errors: list[str]) -> None:
 waivers={item["id"]:item for item in groups["waivers"] if _ident(item.get("id"),"WAIVER")}; used: dict[str,set[str]]={}
 for item in groups["requirements"]:
  status,waiver_id=item.get("status"),item.get("waiver_id")
  if status==PASS:
   if waiver_id is not None: errors.append(f"requirements:{item.get('id')} has an unused waiver_id")
  elif status=="WAIVED" and _ident(waiver_id,"WAIVER") and waiver_id in waivers: used.setdefault(waiver_id,set()).add(item.get("id"))
  elif status=="WAIVED": errors.append(f"requirements:{item.get('id')} has an unknown waiver_id")
  else: errors.append(f"requirements:{item.get('id')} must PASS or be WAIVED")
 for waiver_id,item in waivers.items():
  scope=_strings(item.get("scope_ids"),"REQ",f"waivers:{waiver_id} scope_ids",errors)
  if set(scope)!=used.get(waiver_id,set()) or not set(scope)<=ids["requirements"]: errors.append(f"waivers:{waiver_id} is unused or has invalid scope")
 for item in groups["residual_risks"]:
  value=item.get("risk_id")
  if not _ident(value,"RISK") or value not in ids["risks"]: errors.append(f"residual_risks:{item.get('id')} has unknown risk_id")
def _file(base: Path, item: dict[str,Any], label: str, errors: list[str]) -> Any:
 try:
  value=item.get("path"); raw=Path(value) if _text(value) else None
  if raw is None or raw.is_absolute(): raise ValueError("path must be report-relative")
  root=base.resolve(strict=True); path=(root/raw).resolve(strict=True)
  if root not in path.parents or not path.is_file(): raise ValueError("path must be a file within the report directory")
  if path.stat().st_size>MAX_EVIDENCE_BYTES: raise ValueError("file exceeds size limit")
  digest=item.get("sha256")
  if not isinstance(digest,str) or re.fullmatch(r"[0-9a-f]{64}",digest) is None: raise ValueError("invalid sha256")
  actual=hashlib.sha256(path.read_bytes()).hexdigest()
 except (OSError,UnicodeError,ValueError,RuntimeError,TypeError) as error: errors.append(f"{label}: {error}"); return None
 if actual!=digest: errors.append(f"{label} sha256 does not match")
 return path
def _json(path: Any, label: str, errors: list[str]) -> Any:
 if path is None: return None
 try: return json.loads(path.read_text())
 except (OSError,UnicodeError,json.JSONDecodeError) as error: errors.append(f"{label}: {error}"); return None
def _proof(report: dict[str,Any], groups: dict[str,list[dict[str,Any]]], base: Path, errors: list[str]) -> None:
 validators={item["id"]:item for item in groups["validators"] if _ident(item.get("id"),"VAL")}
 for item in groups["evidence"]:
  path=_file(base,item,f"evidence:{item.get('id')}",errors); validator_id=item.get("validator_id"); validator=validators.get(validator_id,{}) if _ident(validator_id,"VAL") else {}; expected={"evidence_id":item.get("id"),"validator_id":validator.get("id"),"validator_scope":validator.get("scope"),"validator_status":validator.get("status"),"expected_exit_code":validator.get("expected_exit_code"),"actual_exit_code":validator.get("actual_exit_code"),"actual_result":validator.get("actual_result"),"kind":item.get("kind"),"check_names":item.get("check_names"),"covers_ids":item.get("covers_ids")}
  if _json(path,f"evidence:{item.get('id')} content",errors)!=expected: errors.append(f"evidence:{item.get('id')} content is not bound to its producer result")
 for item in groups["artifacts"]: _file(base,item,f"artifacts:{item.get('id')}",errors)
 human=report.get("human_report")
 if not _shape(human,{"id","path","sha256","status"},"human_report",errors): human={}
 plan=report.get("plan"); plan_status=plan.get("status") if isinstance(plan,dict) else None
 if not _ident(human.get("id"),"REPORT") or human.get("status")!=plan_status: errors.append("human_report is invalid or disagrees with plan")
 expected={"plan_id":plan.get("id") if isinstance(plan,dict) else None,"status":plan_status,"checks":report.get("checks"),"check_evidence":report.get("check_evidence")}; path=_file(base,human,"human_report",errors)
 if _json(path,"human_report content",errors)!=expected: errors.append("human_report content disagrees with machine report")
 for item in groups["baselines"]:
  if type(item.get("expected_exit_code")) is not int or type(item.get("actual_exit_code")) is not int or item.get("actual_exit_code")!=item.get("expected_exit_code"): errors.append(f"baselines:{item.get('id')} exit code mismatch")
 checks=report.get("checks"); evidence=report.get("check_evidence")
 if not isinstance(checks,dict) or set(checks)!=set(CHECKS) or any(value is not True for value in checks.values()): errors.append("checks must contain exactly true required values")
 if not isinstance(evidence,dict) or set(evidence)!=set(CHECKS): errors.append("check_evidence must contain exact required keys")
def _aggregates(report: dict[str,Any], groups: dict[str,list[dict[str,Any]]], ids: dict[str,set[str]], errors: list[str]) -> None:
 evidence={item["id"]:item for item in groups["evidence"] if _ident(item.get("id"),"EVID")}; validators={item["id"]:item for item in groups["validators"] if _ident(item.get("id"),"VAL")}; check_evidence=report.get("check_evidence") if isinstance(report.get("check_evidence"),dict) else {}
 plan=report.get("plan"); human=report.get("human_report"); plan_id=plan.get("id") if isinstance(plan,dict) and _ident(plan.get("id"),"PLAN") else ""; report_id=human.get("id") if isinstance(human,dict) and _ident(human.get("id"),"REPORT") else ""
 required={"all_requirements_pass":ids["requirements"], "all_required_validators_pass":ids["validators"], "all_required_artifacts_exist":ids["artifacts"], "all_changed_files_accounted_for":ids["changed_files"], "all_required_gates_pass":ids["gates"], "all_blockers_closed":{plan_id}, "no_unapproved_scope_change":ids["changed_files"]|{item["id"] for item in groups["gates"] if item.get("type")=="approval" and _ident(item.get("id"),"GATE")}, "human_and_machine_reports_match":{plan_id,report_id}, "rollback_and_cleanup_complete":ids["risks"]|ids["residual_risks"]|ids["cleanup"], "independent_review_pass":ids["reviews"]}
 used:set[str]=set()
 for name in CHECKS:
  linked=_strings(check_evidence.get(name),"EVID",f"check_evidence:{name}",errors); used.update(linked); covered:set[str]=set()
  for evidence_id in linked:
   item=evidence.get(evidence_id,{}); validator=validators.get(item.get("validator_id"),{}) if _ident(item.get("validator_id"),"VAL") else {}
   if validator.get("scope")!="whole-plan" or not _text(item.get("kind")) or item.get("kind") not in KINDS[name] or name not in _list(item.get("check_names")): errors.append(f"check_evidence:{name} has invalid scope, kind, or producer result")
   covered.update(value for value in _list(item.get("covers_ids")) if isinstance(value,str))
  if not required[name]<=covered: errors.append(f"check_evidence:{name} misses structured coverage")
 for name in LINKS:
  for item in groups[name]:
   values=item.get("evidence_ids") if isinstance(item.get("evidence_ids"),list) else []
   used.update(value for value in values if _ident(value,"EVID"))
 if ids["evidence"]!=used: errors.append("evidence contains missing or orphan ids")
 if not any(item.get("type")=="independent" and item.get("status")==PASS for item in groups["reviews"]): errors.append("independent review is missing")
def validate(report: Any, report_path: Path) -> list[str]:
 if not isinstance(report,dict): return ["report must be an object"]
 errors:list[str]=[]; _header(report,errors); groups,ids=_records(report,errors); _links(groups,ids,errors); _statuses(groups,ids,errors)
 plan=report.get("plan"); human=report.get("human_report"); plan_id=plan.get("id") if isinstance(plan,dict) and _ident(plan.get("id"),"PLAN") else ""; report_id=human.get("id") if isinstance(human,dict) and _ident(human.get("id"),"REPORT") else ""
 _graph(groups,ids,plan_id,report_id,errors); _waivers(groups,ids,errors); _proof(report,groups,report_path.parent,errors); _aggregates(report,groups,ids,errors)
 return errors
def main() -> int:
 if len(sys.argv)!=2: print("usage: validate_completion_report.py REPORT.json",file=sys.stderr); return 2
 path=Path(sys.argv[1])
 try: report=json.loads(path.read_text())
 except (OSError,UnicodeError,json.JSONDecodeError) as error: print(f"BLOCKED: {error}",file=sys.stderr); return 2
 errors=validate(report,path)
 for error in errors: print(f"BLOCKED: {error}",file=sys.stderr)
 if errors: return 1
 print(PASS); return 0
if __name__=="__main__": raise SystemExit(main())
