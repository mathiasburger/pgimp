# Gimp documentation

Gimp offers a method to dump the whole procedural database:

```
pdb.gimp_procedural_db_dump(filename)
```

Query the db for contents:

```
# search for procedure
num_matches, procedure_names = \
    pdb.gimp_procedural_db_query(name, blurb, help, author, copyright, date, proc_type)

# get all procedures
num_matches, procedure_names = \
    pdb.gimp_procedural_db_query('', '', '', '', '', '', '')
```

Information about a procedure can be gathered as follows:

```
blurb, help, author, copyright, date, proc_type, num_args, num_values = \
    pdb.gimp_procedural_db_proc_info('gimp-procedural-db-proc-info')
```

Information about arguments can be retrieved as follows:

```
arg_type, arg_name, arg_desc = \
    pdb.gimp_procedural_db_proc_arg(procedure_name, arg_num)
```

Information about return values can be retrieved as follows:

```
val_type, val_name, val_desc = \
    pdb.gimp_procedural_db_proc_val(procedure_name, val_num)
```

