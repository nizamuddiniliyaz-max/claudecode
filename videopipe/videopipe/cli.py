import argparse
from pathlib import Path

from . import analyze, candidates, project, report, research


def main(argv=None):
    p = argparse.ArgumentParser(prog="vp", description="Local-first video repurposing (milestone 1)")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("init", help="create project folder, copy source, hash, probe")
    a.add_argument("video"); a.add_argument("--root", default="VideoProjects"); a.add_argument("--name")
    a = sub.add_parser("transcribe", help="WhisperX transcript (local)")
    a.add_argument("project"); a.add_argument("--model", default="small")
    a.add_argument("--device", default="auto"); a.add_argument("--no-diarize", action="store_true")
    a.add_argument("--min-speakers", type=int); a.add_argument("--max-speakers", type=int)
    a = sub.add_parser("analyze", help="filler/pause/repeat proposals (local)")
    a.add_argument("project")
    a = sub.add_parser("research", help="YouTube research (sends query strings off-device)")
    a.add_argument("project"); a.add_argument("queries", nargs="+")
    a = sub.add_parser("candidates", help="rank clips via hosted LLM (sends transcript text off-device)")
    a.add_argument("project")
    a = sub.add_parser("report", help="markdown ranked table")
    a.add_argument("project")
    args = p.parse_args(argv)
    proj = Path(getattr(args, "project", "."))
    if args.cmd == "init":
        print(project.init_project(Path(args.video), Path(args.root), args.name))
    elif args.cmd == "transcribe":
        from . import transcribe
        print(transcribe.transcribe(proj, args.model, args.device, not args.no_diarize,
                                    args.min_speakers, args.max_speakers))
    elif args.cmd == "analyze":
        print(analyze.run(proj))
    elif args.cmd == "research":
        print(research.run(proj, args.queries))
    elif args.cmd == "candidates":
        print(candidates.run(proj))
    elif args.cmd == "report":
        print(report.run(proj))


if __name__ == "__main__":
    main()
