import requests
import asyncio
import sys
import argparse

SCRIPT_VERSION = '1.0'

NUGET_SEARCH_ENDPOINT_URL = 'https://azuresearch-ussc.nuget.org/query'
DEFAULT_SEARCH_TAKE = 15
NUGET_SEARCH_MAX_TAKE = 1000


async def make_nuget_query(params: dict):
    return requests.get(NUGET_SEARCH_ENDPOINT_URL, params = params)


def int_gt_zero(argument):
    num = int(argument)
    if num <= 0:
        raise argparse.ArgumentTypeError(f"{num} is an invalid integer value > 0")
    return num


async def main():
    parser = argparse.ArgumentParser(description = 'Search for NuGet packages', add_help = False)
    parser.add_argument("query", help="The search string passed to the NuGet Search API")
    parser.add_argument("-h", "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit."
    )
    parser.add_argument("-V", "--version",
        action="version",
        version=SCRIPT_VERSION,
        default=argparse.SUPPRESS,
        help="Show the script version and exit."
    )
    parser.add_argument("-a", "--show-all",
        action="store_true",
        help="Keep fetching results until all results are retrieved. This overrides the --max-results option."
        )
    parser.add_argument("-m", "--max-results",
        type=int_gt_zero,
        metavar='N',
        default=DEFAULT_SEARCH_TAKE,
        help="Set the max number of results to be fetched."
        )
    parser.add_argument("-v", "--verbose",
        action="store_true",
        help="Display additional information about every package resulting from the search."
        )
    parser.add_argument("-s", "--show-all-versions",
        action="store_true",
        help="Display all available versions of packages."
        )
    args = parser.parse_args()

    num_results = -1
    total_results = 0
    skip = 0
    packages = list()
    
    while True:
        query_params = {
            "q": args.query,
            "take": min(NUGET_SEARCH_MAX_TAKE, args.max_results), 
            "skip": skip
            }
        
        response = await make_nuget_query(query_params)
        if response.status_code != 200:
            sys.exit(1)
        
        response_data = response.json()

        if num_results < 0:
            total_results = response_data.get("totalHits", 0)
            if args.show_all:
                num_results = total_results
            else:
                num_results = min(total_results, args.max_results)
        
        fetched_pkgs = response_data.get("data", list())
        skip += len(fetched_pkgs)
        
        packages.extend(fetched_pkgs)
        if skip >= num_results:
            break

    indent = 0
    for pkg in packages:
        print('> ', pkg["id"])
        
        if args.verbose:
            indent += 2
            print(' ' * indent, "Type: ".ljust(10), pkg.get("@type", "Unknown"))
            print(' ' * indent, "Owners: ".ljust(10), ', '.join(pkg.get("owners", list())))
            print(' ' * indent, "Downloads: ".ljust(10), str(pkg.get("totalDownloads", 0)))
            print(' ' * indent, "URL: ".ljust(10), str(pkg.get("projectUrl", "Unknown")))
            print(' ' * indent, "Verified: ".ljust(10), str(pkg.get("verified", False)))
        
        if args.show_all_versions:
            indent += 2
            for version in pkg.get("versions", list()):
                print(' ' * indent, '+', version["version"].ljust(16), 'Downloads: ', version["downloads"])
        
        if indent > 0:
            print()
        
        indent = 0

    print(f"\nTotal of {total_results} results, {num_results} displayed...")
    sys.exit(0)


if __name__ == '__main__':
    asyncio.run(main())
