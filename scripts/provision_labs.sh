#!/usr/bin/env bash
#
# provision_labs.sh - create one private lab repository per student.
#
#     bash scripts/provision_labs.sh --dry-run      # show what it would do
#     bash scripts/provision_labs.sh                # do it
#     bash scripts/provision_labs.sh --roster FILE  # non-default roster
#
# INSTRUCTOR ONLY. Students never run this.
#
# ---------------------------------------------------------------------------
# WHY THIS EXISTS
#
# GitHub Classroom did precisely this, and was retired on 2026-08-28 - sign-ups
# closed 2026-05-26, the service went dark 08-28, residual data deleted 09-04.
# Its own retirement notice points out that the repositories and organisations
# it created are unaffected, because they were always just org repositories.
# This script is the thirty lines that were underneath it.
#
# The alternative - each student creates their own private repository and adds
# the instructor - is 24 chances a week-one mistake goes unnoticed:
#
#   left public          -> publishes this course's lab solutions to next year
#   collaborator typo    -> discovered when the work is already due
#   deleted after grades -> no artifact for a dispute
#
# One script, run once, before anyone opens a terminal.
#
# ---------------------------------------------------------------------------
# RUNBOOK
#
# Once per course:
#   1. Create a FREE GitHub organisation (github.com, ~2 min - the REST API
#      cannot create organisations for personal accounts).
#
#      It must be FREE, not Team. On a paid plan every outside collaborator on a
#      private repository consumes a seat regardless of permission level, so 24
#      students would be ~24 seats. GitHub Free for organisations gives
#      unlimited private repositories and unlimited collaborators.
#
#   2. Set COURSE_ORG in scripts/lab_report.py to its name.
#
# Once per term:
#   3. Set COURSE_TERM in scripts/lab_report.py.
#   4. Collect GitHub usernames - one form, first class - into the roster:
#
#          course/roster-<term>.txt
#          # uniqname   github-username
#          jdoe         janedoe99
#
#      Git-ignored, and it must stay that way: this repository is public.
#
#      UNIQNAME and GITHUB USERNAME ARE DIFFERENT THINGS, and the roster exists
#      to map one to the other:
#
#        uniqname          umich-assigned, the part before @umich.edu. Names the
#                          repository, so a repo maps to a gradebook row without
#                          a lookup.
#        github username   self-chosen, arbitrary, changeable. The only thing
#                          GitHub will accept when granting access.
#
#      Ask for the profile URL rather than the username - same information, but
#      a student copies it from the address bar instead of recalling it, and
#      whatever is in that URL IS their username by definition. Someone who made
#      the account last week may not know which of their display name, login and
#      signup email is the one being asked for. Either form works below.
#
#      Converting a form export (uniqname in column 3, GitHub in column 4):
#
#        awk -F, 'NR>1 {
#            u=$3; g=$4
#            gsub(/^[ \t]+|[ \t]+$/, "", u); gsub(/^[ \t]+|[ \t]+$/, "", g)
#            sub(/^.*github\.com\//, "", g)   # URL -> path; bare name untouched
#            sub(/\?.*$/, "", g)              # drop ?tab=repositories
#            sub(/\/.*$/, "", g)              # keep ONLY the first path segment
#            sub(/^@/, "", g)                 # people write @handle
#            if (u != "" && g != "") printf "%-12s %s\n", u, g
#        }' responses.csv > course/roster-<term>.txt
#
#   5. Run with --dry-run FIRST and read the account-name column. A username
#      that resolves is not necessarily the right person, and this is the only
#      point at which a wrong one is still harmless.
#
#   6. Run it for real. Re-run whenever a student registers late; it is
#      idempotent and will create nothing that already exists.
#
#   7. Tell students their repository exists and to accept the invitation.
#      `bash scripts/lab.sh init` derives the URL, so they press Enter.
#
# Students get `push`, not `admin`: they commit freely and cannot change
# visibility or delete the repository. That asymmetry is the entire point.
#
# Uses `gh api` rather than `gh repo create` on purpose - the `repo create`
# flags have drifted across gh versions (this machine has 2.4.0) while the REST
# endpoints have not.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

if [ -t 1 ]; then
    G=$'\033[32m'; R=$'\033[31m'; Y=$'\033[33m'; B=$'\033[1m'; N=$'\033[0m'
else
    G=""; R=""; Y=""; B=""; N=""
fi

DRY=0
ROSTER=""
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY=1 ;;
        --roster)  ROSTER="${2:-}"; shift ;;
        -h|--help) sed -n '2,6p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done

# The org, term and naming scheme live in exactly one place. Read them from it
# rather than duplicating, so they cannot drift apart.
read -r ORG TERM_SLUG PREFIX <<EOF
$(python3 -c "
import sys; sys.path.insert(0, 'scripts')
import lab_report as L
print(L.COURSE_ORG, L.COURSE_TERM, L.REPO_PREFIX)
")
EOF
[ -n "${ORG:-}" ] || { echo "could not read COURSE_ORG from scripts/lab_report.py" >&2; exit 1; }

[ -n "$ROSTER" ] || ROSTER="course/roster-${TERM_SLUG}.txt"
if [ ! -f "$ROSTER" ]; then
    cat >&2 <<EOF
${R}no roster at${N} $ROSTER

Create it - one line per student, git-ignored:

    # uniqname   github-username
    jdoe         janedoe99
EOF
    exit 1
fi

command -v gh >/dev/null 2>&1 || { echo "gh not found" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "gh not authenticated. Run: gh auth login" >&2; exit 1; }

if ! gh api "orgs/${ORG}" >/dev/null 2>&1; then
    echo "${R}cannot see organisation ${ORG}${N}" >&2
    echo "Create it at https://github.com/organizations/plan (choose Free), then" >&2
    echo "set COURSE_ORG in scripts/lab_report.py." >&2
    exit 1
fi

PLAN="$(gh api "orgs/${ORG}" -q '.plan.name // "unknown"' 2>/dev/null)"
if [ "$PLAN" != "free" ] && [ "$PLAN" != "unknown" ]; then
    printf "%sWARN%s  %s is on the '%s' plan. Outside collaborators on private repos\n" \
        "$Y" "$N" "$ORG" "$PLAN"
    printf "      consume a paid seat each - one per student. A Free org does not.\n\n"
fi

printf "%sorg%s     %s   %splan%s %s\n" "$B" "$N" "$ORG" "$B" "$N" "$PLAN"
printf "%sterm%s    %s\n" "$B" "$N" "$TERM_SLUG"
printf "%sroster%s  %s\n\n" "$B" "$N" "$ROSTER"
if [ "$DRY" = 1 ]; then
    printf "%s-- dry run: nothing will be created --%s\n\n" "$Y" "$N"
    # Read the third column. A username that resolves is not necessarily the
    # RIGHT person, and this is the only chance to notice before a stranger is
    # invited into a student's private repository.
    printf "      %-38s %-16s %s\n" "repository" "github user" "account name"
    printf "      %-38s %-16s %s\n" "----------" "-----------" "------------"
fi

CREATED=0; EXISTED=0; INVITED=0; FAILED=0

while read -r line; do
    line="${line%%#*}"
    # shellcheck disable=SC2086
    set -- $line
    [ $# -ge 1 ] || continue
    UNIQ="$1"
    GHUSER="${2:-}"
    if [ -z "$GHUSER" ]; then
        printf "%sFAIL%s  %-12s no github username in the roster\n" "$R" "$N" "$UNIQ"
        FAILED=$((FAILED + 1))
        continue
    fi

    NAME="${PREFIX}-${TERM_SLUG}-${UNIQ}"

    # Resolve the GitHub account BEFORE creating anything.
    #
    # Two reasons, and the second is the serious one:
    #
    #   1. A typo used to create the repository and then fail to add anyone,
    #      leaving an orphan nobody can reach.
    #   2. A typo that happens to name a REAL DIFFERENT PERSON silently invites
    #      a stranger into a student's private repository. Students type these
    #      into a form from memory, and GitHub display names, usernames and
    #      emails all look alike. Printing the account's real name is what lets
    #      you catch "jdoe -> jsmith (Unrelated Person)" by eye.
    REALNAME="$(gh api "users/${GHUSER}" -q '.name // .login' 2>/dev/null)"
    if [ -z "$REALNAME" ]; then
        printf "%sFAIL%s  %-34s no GitHub user '%s'\n" "$R" "$N" "$NAME" "$GHUSER"
        FAILED=$((FAILED + 1))
        continue
    fi

    if [ "$DRY" = 1 ]; then
        printf "      %-38s %-16s %s\n" "$NAME" "$GHUSER" "\"$REALNAME\""
        continue
    fi

    if gh api "repos/${ORG}/${NAME}" >/dev/null 2>&1; then
        printf "%sok%s    %-34s exists" "$G" "$N" "$NAME"
        EXISTED=$((EXISTED + 1))
    else
        if gh api "orgs/${ORG}/repos" -X POST \
                -f "name=${NAME}" \
                -F "private=true" \
                -f "description=Lab submissions - ${UNIQ} - MRider ${TERM_SLUG}" \
                -F "has_issues=false" -F "has_wiki=false" -F "has_projects=false" \
                >/dev/null 2>&1; then
            printf "%sok%s    %-34s created" "$G" "$N" "$NAME"
            CREATED=$((CREATED + 1))
        else
            printf "%sFAIL%s  %-34s could not create\n" "$R" "$N" "$NAME"
            FAILED=$((FAILED + 1))
            continue
        fi
    fi

    # Always re-assert: harmless when already a collaborator, and it repairs a
    # roster corrected after a username typo.
    if gh api "repos/${ORG}/${NAME}/collaborators/${GHUSER}" -X PUT \
            -f "permission=push" >/dev/null 2>&1; then
        printf ", %s (%s) has push\n" "$GHUSER" "$REALNAME"
        INVITED=$((INVITED + 1))
    else
        printf ", %scould not add %s%s\n" "$R" "$GHUSER" "$N"
        FAILED=$((FAILED + 1))
    fi
done < "$ROSTER"

if [ "$DRY" = 1 ]; then
    printf "\n%sDry run complete.%s Re-run without --dry-run to apply.\n" "$B" "$N"
    exit 0
fi

printf "\n%s================================================================%s\n" "$B" "$N"
printf " %d created, %d already existed, %d collaborators asserted, %d failed\n" \
    "$CREATED" "$EXISTED" "$INVITED" "$FAILED"
printf "%s================================================================%s\n" "$B" "$N"
printf "\nStudents must ACCEPT the invitation before they can push:\n"
printf "    https://github.com/notifications\n"
printf "\nThen, in their clone of the course repository:\n"
printf "    bash scripts/lab.sh init      # the URL is derived; press Enter\n"

[ "$FAILED" -gt 0 ] && exit 1
exit 0
