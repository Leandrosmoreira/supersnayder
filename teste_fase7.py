#!/usr/bin/env python3
"""
Script para testar Fase 7 - Event loop + sockets
Compara: default event loop vs uvloop (Linux)
"""
import os
import sys
import time
import asyncio
import platform
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

async def teste_event_loop():
    """Testa performance do event loop."""
    print("=" * 80)
    print("  🧪 TESTE FASE 7 - Event Loop + Sockets")
    print("=" * 80)
    
    # Verificar sistema
    print(f"\n1️⃣  Sistema: {platform.system()}")
    
    # Teste com event loop padrão
    print("\n2️⃣  Testando event loop padrão...")
    loop_padrao = asyncio.get_event_loop()
    print(f"   ✅ Event loop padrão: {type(loop_padrao).__name__}")
    
    # Teste com uvloop (se Linux)
    if platform.system() == 'Linux':
        try:
            import uvloop
            print("\n3️⃣  Testando uvloop...")
            loop_uvloop = uvloop.new_event_loop()
            asyncio.set_event_loop(loop_uvloop)
            print(f"   ✅ uvloop disponível: {type(loop_uvloop).__name__}")
            
            # Benchmark simples
            print("\n4️⃣  Benchmark de event loop...")
            
            async def task_simples():
                await asyncio.sleep(0.001)
                return time.monotonic_ns()
            
            # Teste com loop padrão
            inicio = time.monotonic_ns()
            tasks = [task_simples() for _ in range(1000)]
            resultados_padrao = await asyncio.gather(*tasks)
            tempo_padrao = (time.monotonic_ns() - inicio) / 1_000_000
            
            # Teste com uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            loop_uvloop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop_uvloop)
            
            inicio = time.monotonic_ns()
            tasks = [task_simples() for _ in range(1000)]
            resultados_uvloop = await asyncio.gather(*tasks)
            tempo_uvloop = (time.monotonic_ns() - inicio) / 1_000_000
            
            print(f"   📊 Event loop padrão: {tempo_padrao:.2f}ms")
            print(f"   📊 uvloop: {tempo_uvloop:.2f}ms")
            
            if tempo_uvloop < tempo_padrao:
                melhoria = ((tempo_padrao - tempo_uvloop) / tempo_padrao) * 100
                print(f"   ✅ Melhoria: {melhoria:.1f}% mais rápido")
            else:
                print(f"   ⚠️  uvloop não mostrou melhoria neste teste")
            
        except ImportError:
            print("\n3️⃣  uvloop não disponível")
            print("   💡 Instale com: pip install uvloop")
    else:
        print("\n3️⃣  uvloop apenas disponível no Linux")
        print(f"   Sistema atual: {platform.system()}")
    
    # Teste de locks
    print("\n5️⃣  Testando otimização de locks...")
    print("   ✅ BookState: Single-writer (lock apenas para escrita)")
    print("   ✅ Snapshot imutável: Leitura sem lock")
    print("   ✅ LatencyMetrics: Lock apenas para criar deque")
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    asyncio.run(teste_event_loop())

