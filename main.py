import nextcord
from nextcord.ext import commands
import os
import wavelink
import asyncio
import datetime
bot = commands.Bot(command_prefix='!', intents=nextcord.Intents.all())

@bot.event
async def on_ready():
    print('Bot is up and ready')
    bot.loop.create_task(node_connect())


async def node_connect():
    await bot.wait_until_ready()
    await wavelink.NodePool.create_node(bot=bot, host="ssl.freelavalink.ga", port=443, password='www.freelavalink.ga', https=True)


@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Node {node.identifier} is ready rightly! lol")

@bot.event
async def on_wavelink_track_end(player: wavelink.Player, track: wavelink.Track, reason):
    ctx = player.ctx
    vc: player = ctx.voice_client

    if vc.loop:
        return await vc.play(track)
    
    try:
        next_song = vc.queue.get()
        await vc.play(next_song)
        emb = nextcord.Embed(title="Playing Next Song", description=f"Now playing [{next_song.title}]({next_song.uri})\nArtist: {next_song.author}")
        await ctx.send(embed=emb)
    except wavelink.QueueEmpty:
        await asyncio.sleep(4)
        await ctx.send("The queue is empty so good bye")
        await vc.disconnect()

@bot.command(aliases=['p'])
async def play(ctx: commands.Context, *, search: wavelink.YouTubeTrack):
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    elif not getattr(ctx.author.voice, "channel", None):
        emb = nextcord.Embed(title='ERROR', description='**Please ensure that you have joined a voice channel**')
        return await ctx.send(embed=emb)
    else:
        vc: wavelink.Player = ctx.voice_client

    if vc.queue.is_empty and not vc.is_playing():
        await vc.play(search)
        emb = nextcord.Embed(title='SUCCESS', description=f'Started playing [{search.title}]({search.uri})\nArtist: {search.author}')
        await ctx.send(embed=emb)
    else:
        await vc.queue.put_wait(search)
        emb = nextcord.Embed(title='SUCCESS', description=f'{search.title} has been added to the queue by {ctx.author.name}')
        await ctx.send(embed=emb)
    vc.ctx = ctx
    setattr(vc, "loop", False)

@bot.command()
async def pause(ctx: commands.Context):
    if not ctx.voice_client:
        emb = nextcord.Embed(title="NO MUSIC IS BEING PLAYED", description='No music is being played. Unable to pause anything')
        return await ctx.send(embed=emb)
    elif not getattr(ctx.author.voice, "channel", None):
        emb = nextcord.Embed(title='ERROR', description='**Please ensure that you have joined a voice channel**')
        return await ctx.send(embed=emb)
    else:
        vc: wavelink.Player = ctx.voice_client
    await vc.pause()
    await ctx.send(embed=nextcord.Embed(title='SUCCESS', description='The music has been paused!'))
        
@bot.command()
async def resume(ctx: commands.Context):
    if not ctx.voice_client:
        emb = nextcord.Embed(title="NO MUSIC IS BEING PLAYED", description='No music is being played. Unable to resume anything')
        return await ctx.send(embed=emb)
    elif not getattr(ctx.author.voice, "channel", None):
        emb = nextcord.Embed(title='ERROR', description='**Please ensure that you have joined a voice channel**')
        return await ctx.send(embed=emb)
    else:
        vc: wavelink.Player = ctx.voice_client
    await vc.resume()
    await ctx.send(embed=nextcord.Embed(title='SUCCESS', description='The music has been resumed!'))

@bot.command()
async def stop(ctx: commands.Context):
    if not ctx.voice_client:
        emb = nextcord.Embed(title="NO MUSIC IS BEING PLAYED", description='No music is being played. Unable to stop anything')
        return await ctx.send(embed=emb)
    elif not getattr(ctx.author.voice, "channel", None):
        emb = nextcord.Embed(title='ERROR', description='**Please ensure that you have joined a voice channel**')
        return await ctx.send(embed=emb)
    else:
        vc: wavelink.Player = ctx.voice_client
    await vc.stop()
    await ctx.send(embed=nextcord.Embed(title='SUCCESS', description='The music has been stopped!'))
        
@bot.command(aliases=['dc', 'leave'])
async def disconnect(ctx: commands.Context):
    if not ctx.voice_client:
        emb = nextcord.Embed(title="NO MUSIC IS BEING PLAYED", description='No music is being played. Unable to disconnect')
        return await ctx.send(embed=emb)
    elif not getattr(ctx.author.voice, "channel", None):
        emb = nextcord.Embed(title='ERROR', description='**Please ensure that you have joined a voice channel**')
        return await ctx.send(embed=emb)
    else:
        vc: wavelink.Player = ctx.voice_client
    await vc.disconnect()
    await ctx.send(embed=nextcord.Embed(title='SUCCESS', description='Thank you for using Posture!'))

@bot.command()
async def loop(ctx: commands.Context):
    if not ctx.voice_client:
        emb = nextcord.Embed(title="NO MUSIC IS BEING PLAYED", description='No music is being played. Unable to pause anything')
        return await ctx.send(embed=emb)
    elif not getattr(ctx.author.voice, "channel", None):
        emb = nextcord.Embed(title='ERROR', description='**Please ensure that you have joined a voice channel**')
        return await ctx.send(embed=emb)
    else:
        vc: wavelink.Player = ctx.voice_client

    try:
        vc.loop ^= True
    except Exception:
        setattr(vc, "loop", False)
    if vc.loop:
        return await ctx.send(embed=nextcord.Embed(title="SUCCESS", description="This song is put to loop!"))
    else:
        return await ctx.send(embed=nextcord.Embed(title="SUCCESS", description="This song is removed from loop!"))

@bot.command(aliases=['playlist'])
async def queue(ctx: commands.Context):
    if not ctx.voice_client:
        emb = nextcord.Embed(title="NO MUSIC IS BEING PLAYED", description='No music is being played. Unable to do anything')
        return await ctx.send(embed=emb)
    elif not getattr(ctx.author.voice, "channel", None):
        emb = nextcord.Embed(title='ERROR', description='**Please ensure that you have joined a voice channel**')
        return await ctx.send(embed=emb)
    else:
        vc: wavelink.Player = ctx.voice_client
    if vc.queue.is_empty:
        return await ctx.send(embed=nextcord.Embed(title="The queue is empty", description="The queue finished"))
    em = nextcord.Embed(title="Song Queue")
    queue = vc.queue.copy()
    song_count = 0
    for song in queue:
        song_count += 1
        em.add_field(name=f"-------------------------------", value=f"{song_count} | [{song.title}]({song.uri}) | Artist: {song.author}", inline=False)
    return await ctx.send(embed=em)
         
@bot.command(aliases=['np'])
async def nowplaying(ctx: commands.Context):
    if not ctx.voice_client:
        emb = nextcord.Embed(title="NO MUSIC IS BEING PLAYED", description='No music is being played. Unable to show anything')
        return await ctx.send(embed=emb)
    elif not getattr(ctx.author.voice, "channel", None):
        emb = nextcord.Embed(title='ERROR', description='**Please ensure that you have joined a voice channel**')
        return await ctx.send(embed=emb)
    else:
        vc: wavelink.Player = ctx.voice_client
    if not vc.is_playing():
        return await ctx.send("There is nothing that is being played!")
    em = nextcord.Embed(title='Now Playing', description=f"[{vc.track.title}]({vc.track.uri})\nArtist: {vc.track.author}")
    em.add_field(name="Duration", value=f'{str(datetime.timedelta(seconds=vc.track.length))}')
    em.set_thumbnail(url=vc.track.thumbnail)
    return await ctx.send(embed=em)

@bot.command()
async def invite(ctx: commands.Context):
    if not ctx.author.id == 716572751825076295:
            return
    await ctx.reply(f'My invite link:- https://discord.com/api/oauth2/authorize?client_id=1075021934519144489&permissions=8&scope=bot%20applications.commands')


bot.run('MTA3NTAyMTkzNDUxOTE0NDQ4OQ.GtihXN.K0p_Tzu_Kojhls3pI6tkLfSKbYVFOV4VN14GPI')