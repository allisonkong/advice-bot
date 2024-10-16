#!/usr/bin/env python3

import discord
import params


def main():
    p = params.GetParams()
    print(p.application_id)


if __name__ == "__main__":
    main()
