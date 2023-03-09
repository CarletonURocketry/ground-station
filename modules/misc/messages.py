# Display for the console window
# Thomas Selwyn (Devil)

def print_cu_rocket(rocket_name: str, version: str, author: str) -> None:

    """Prints the CUInSpace rocket ASCII art with information about the rocket and software version."""

    print(fr"""
           ^
          / \
         /___\
        |=   =|              |\___/|
        |     |             /       \
        | C U |             |    /\__/|
        | I N |             ||\  <.><.>
        |Space|             | _     > )
        |     |             \   /----
        |     |              |   -\/
       /|##!##|\             /     \
      / |##!##| \
     /  |##!##|  \
    |  / ^ | ^ \  |
    | /  ( | )  \ |
    |/   ( | )   \|
        ((   ))
       ((  :  ))            CU InSpace Avionics Telemetry Server
       ((  :  ))            {f"Rocket": <11}{rocket_name}
        ((   ))             {f"Version": <11}{version}
          ( )               {f"Author": <11}{author}
              """)
