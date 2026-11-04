def validate_mapping(taxonomy,mapping):
    if mapping.get('status')!='mapped': return
    levels=[('paper_id','paper'),('chapter_id','chapter'),('topic_id','topic'),('subtopic_id','subtopic')]
    nodes=[]
    for key,level in levels:
        node=taxonomy.get(mapping[key])
        if node.get('level')!=level: raise ValueError(f'{mapping[key]} is not a {level}')
        nodes.append(node)
    if nodes[1].get('parent_id')!=nodes[0]['id'] or nodes[2].get('parent_id')!=nodes[1]['id'] or nodes[3].get('parent_id')!=nodes[2]['id']:
        raise ValueError('Invalid taxonomy hierarchy')
    for cid in [mapping.get('primary_concept_id'),*(mapping.get('secondary_concept_ids') or [])]:
        if cid:
            c=taxonomy.get(cid)
            if c.get('level')!='concept' or c.get('parent_id')!=nodes[3]['id']: raise ValueError(f'Invalid concept hierarchy: {cid}')
