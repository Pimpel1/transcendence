export class TournamentSession {
    constructor(tournamentData) {
        this.update(tournamentData);
    }

    update(tournamentData) {
        const {
            name,
            id,
            type,
            pool_size,
            players,
            status,
            current_round,
            winner,
            ranking,
            leaderboard,
            games,
        } = tournamentData;

        this.name = name;
        this.id = id;
        this.type = type;
        this.poolSize = pool_size;
        this.players = players;
        this.status = status;
        this.currentRound = current_round;
        this.winner = winner;
        this.ranking = ranking;
        this.leaderboard = leaderboard;
        this.games = games;
    }
}